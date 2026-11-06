import { useEffect, useId, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import type { Chamado, EvalResumo, Fila, LinhaFila, Numero, Resultado } from './tipos'
import { ACAO, CAUSA, FONTE, REGRA, STATUS, TIPO, nomeModelo, pct, reais } from './textos'

const REPO = 'https://github.com/levifb/estagiogogroup'
const LIMITACOES = `${REPO}#limitações-e-próximos-passos`
const TEMPO_LIMITE_MS = 25_000
// Campos comuns a todo chamado; os específicos de cada causa (ex.: brinde no CD2) aparecem primeiro.
const GERAIS = new Set([
  'tipos de exceção', 'exceções deste tipo no grupo', 'mesma proporção nos demais grupos',
  'vezes acima dos demais', 'exceções além do esperado', 'valor pago dos pedidos afetados',
])

async function carregar<T>(arquivo: string): Promise<T | null> {
  try {
    const r = await fetch(`/data/${arquivo}`)
    return r.ok ? ((await r.json()) as T) : null
  } catch {
    return null
  }
}

type Numeros = Record<string, Numero>

/** Número do registro (docs/numeros.json), nunca digitado. O título mostra a definição. */
function N({ n, id }: { n: Numeros; id: string }) {
  const x = n[id]
  if (!x) return <span className="num">…</span>
  return (
    <abbr className="num" title={`${x.definicao}${x.estimativa ? ' (estimativa)' : ''}. Fonte: ${id} em docs/NUMEROS.md`}>
      {x.texto}
    </abbr>
  )
}

/** Balão com a definição dos números de um cartão. É um botão, então funciona no toque e no teclado. */
function Definicao({ n, ids }: { n: Numeros; ids: string[] }) {
  const [aberto, setAberto] = useState(false)
  const idPainel = useId()
  return (
    <div className="def">
      <button type="button" className="def-botao" aria-expanded={aberto} aria-controls={idPainel} onClick={() => setAberto(!aberto)}>
        {aberto ? 'Fechar a conta' : 'Como calculamos'}
      </button>
      <div id={idPainel} className="def-painel" hidden={!aberto}>
        {ids.map((id) =>
          n[id] ? (
            <p key={id}>
              <b className="mono">{n[id].texto}</b> {n[id].definicao}
              {n[id].estimativa ? ' (estimativa)' : ''}. <span className="def-id">{id} em docs/NUMEROS.md</span>
            </p>
          ) : null,
        )}
      </div>
    </div>
  )
}

function Passo({ n, children, id, comoTexto }: { n: number; children: ReactNode; id?: string; comoTexto?: boolean }) {
  const conteudo = (
    <>
      <span className="passo-n mono">{n}.</span> {children}
    </>
  )
  // O passo 1 fica como rótulo: o título da página (h1) é a frase do problema logo abaixo.
  return comoTexto ? <p className="passo" id={id}>{conteudo}</p> : <h2 className="passo" id={id}>{conteudo}</h2>
}

export default function App() {
  const [numeros, setNumeros] = useState<Numeros>({})
  const [fila, setFila] = useState<Fila | null>(null)
  const [chamados, setChamados] = useState<Chamado[]>([])
  const [ev, setEv] = useState<EvalResumo | null>(null)
  const [sel, setSel] = useState<string | null>(null)
  const [filtro, setFiltro] = useState<'todos' | 'humano' | 'sozinho'>('todos')

  useEffect(() => {
    carregar<{ numeros: Numeros }>('numeros.json').then((d) => d && setNumeros(d.numeros))
    carregar<Fila>('fila.json').then((d) => {
      if (!d) return
      setFila(d)
      setSel(d.casos[0]?.order_id ?? null)
    })
    carregar<Chamado[]>('chamados.json').then((d) => d && setChamados(d))
    carregar<EvalResumo>('eval.json').then(setEv)
  }, [])

  const casos = fila?.casos ?? []
  const humanos = casos.filter((c) => c.humano).length
  const pendentes = casos.filter((c) => c.pendente).length
  const sozinhos = casos.length - humanos - pendentes
  const visiveis = useMemo(
    () => casos.filter((c) => (filtro === 'todos' ? true : filtro === 'humano' ? c.humano : !c.humano && !c.pendente)),
    [casos, filtro],
  )
  const dia = fila?.data_referencia ?? '30/09/2026'
  const painel = useRef<HTMLDivElement>(null)

  function escolher(id: string) {
    setSel(id)
    // Em tela estreita o detalhe fica abaixo da lista: leva a pessoa até ele.
    if (window.matchMedia('(max-width: 960px)').matches) {
      requestAnimationFrame(() => painel.current?.scrollIntoView({ block: 'start' }))
    }
  }

  return (
    <div id="topo">
      <a className="pular" href="#fila">Pular para a fila de hoje</a>
      <header className="nav">
        <div className="nav-in wrap">
          <a className="marca" href="#topo">
            <svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true">
              <rect width="32" height="32" rx="6" fill="#0b1f3a" />
              <rect x="7" y="9" width="18" height="3" fill="#fff" />
              <rect x="7" y="15" width="13" height="3" fill="#fff" />
              <rect x="7" y="21" width="8" height="3" fill="#c5e83a" />
            </svg>
            Mesa de exceções
          </a>
          <nav className="nav-links" aria-label="Seções">
            <a href="#impacto">Impacto</a>
            <a href="#fila">Fila de hoje</a>
            <a href="#causas">Causas</a>
          </nav>
          <a className="nav-repo" href={REPO}>Código no GitHub</a>
        </div>
      </header>

      <main>
        <section className="problema wrap" aria-labelledby="t-problema">
          <Passo n={1} comoTexto>O problema</Passo>
          <h1 className="manchete" id="t-problema">
            Há <N n={numeros} id="N01" /> exceções de pedido abertas, o que dá <N n={numeros} id="N05" /> dias de fila para a
            equipe. Tratadas por ordem de chegada, elas custam <N n={numeros} id="N70" /> em
            perda esperada.
          </h1>
          <p className="lead">
            A Mesa de exceções monta o plano do dia com os {casos.length || '…'} casos que mais pioram se esperarem. Um agente de
            IA decide cada caso e escreve a mensagem ao cliente. A analista revisa só os casos que as regras mandam, e as causas
            que se repetem viram chamados para quem pode corrigi-las.
          </p>
          <div className="acoes">
            <a className="btn btn-primario" href="#fila">Abrir a fila de hoje</a>
            <a className="btn btn-linha" href={REPO}>Ver o código</a>
          </div>
          <p className="contexto">
            Juliana, a analista, é uma persona fictícia. Dados sintéticos do Desafio AI-First do Gogroup, fila de {dia}; as
            ações são simuladas e nada é enviado a clientes.
          </p>
        </section>

        <section className="impacto" id="impacto" aria-labelledby="t-impacto">
          <div className="wrap">
            <Passo n={2} id="t-impacto">Impacto</Passo>
            <div className="cartoes">
              <article className="cartao">
                <p className="valor mono"><N n={numeros} id="N72" /></p>
                <p className="frase">a menos de perda esperada com o plano do dia, contra a ordem de chegada.</p>
                <p className="sub">
                  Estimativa, de uma vez, sobre a fila acumulada até {dia}: <N n={numeros} id="N73" /> a menos. Não é um ganho
                  mensal.
                </p>
                <Definicao n={numeros} ids={['N72', 'N70', 'N71']} />
              </article>
              <article className="cartao">
                <p className="valor mono">
                  <N n={numeros} id="N104" /> <span className="de">de <N n={numeros} id="N100" /></span>
                </p>
                <p className="frase">casos de hoje decididos pelo agente sem a analista.</p>
                <p className="sub">
                  São <N n={numeros} id="N105" /> de trabalho do time por dia que deixam de ser decisão e viram revisão
                  (estimativa).
                </p>
                <Definicao n={numeros} ids={['N104', 'N105']} />
              </article>
              <article className="cartao">
                <p className="valor mono"><N n={numeros} id="N97" /></p>
                <p className="frase">exceções por mês que deixam de existir com mudanças de processo.</p>
                <p className="sub">
                  São <N n={numeros} id="N99" /> mudanças, cada uma com um dono (estimativa).
                </p>
                <Definicao n={numeros} ids={['N97', 'N99']} />
              </article>
              <article className="cartao">
                <p className="valor mono"><N n={numeros} id="N23" /></p>
                <p className="frase">dos “atrasos” são erro do checkout, e não da transportadora.</p>
                <p className="sub">
                  A data prometida ao cliente é calculada em dias corridos, mas o prazo contratado com a transportadora é em
                  dias úteis.
                </p>
                <Definicao n={numeros} ids={['N23', 'N22', 'N20']} />
              </article>
            </div>
          </div>
        </section>

        <section className="wrap bloco-sec" aria-labelledby="t-antes">
          <Passo n={3} id="t-antes">Antes e depois</Passo>
          <table className="antes">
            <thead>
              <tr>
                <th scope="col"><span className="sr">Tema</span></th>
                <th scope="col">Hoje</th>
                <th scope="col">Com a Mesa de exceções</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">Ordem</th>
                <td>A fila anda por ordem de chegada. Um pedido que vai piorar amanhã espera atrás de outro que já não piora.</td>
                <td>Um plano diário põe primeiro os casos que mais pioram se esperarem, dentro da capacidade do time.</td>
              </tr>
              <tr>
                <th scope="row">Decisão</th>
                <td>A analista decide todos os <span className="mono">{casos.length || '…'}</span> casos do dia, um por um, em telas diferentes.</td>
                <td>
                  O agente decide e escreve a mensagem. A analista revisa os <span className="mono">{humanos}</span> casos que as regras mandam, cada um com
                  o motivo.
                </td>
              </tr>
              <tr>
                <th scope="row">Causas</th>
                <td>Causas que se repetem ficam invisíveis, porque cada caso é tratado sozinho.</td>
                <td><span className="mono">{chamados.length || '…'}</span> chamados com dono e evidência, para a causa parar de gerar exceções.</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section className="wrap bloco-sec" id="prova" aria-labelledby="t-prova">
          <Passo n={4} id="t-prova">Como sabemos que é verdade</Passo>
          <ul className="provas">
            {ev && (
              <li>
                <b>Gabarito.</b> Em {ev.resumo.n} casos com a resposta certa pela política, o agente escolheu a ação certa em{' '}
                <span className="mono">{ev.resumo.acao_aceitavel}</span> e mandou para a pessoa{' '}
                <span className="mono">{ev.resumo.recall_humano[0]} de {ev.resumo.recall_humano[1]}</span> casos de risco. Uma
                automação com ação fixa por tipo acerta <span className="mono">{ev.resumo.linha_de_base_aceitavel}</span>.
              </li>
            )}
            <li>
              <b>Fila de hoje.</b> <N n={numeros} id="N101" /> das <N n={numeros} id="N100" /> decisões batem com a tabela de
              política, numa conferência automática.
            </li>
            <li>
              <b>Testes.</b> Prazos em dias úteis, risco, plano do dia, regras de revisão e troca de modelo têm testes
              automáticos (<code>python -m pytest</code>).
            </li>
            <li>
              <b>Avaliador cego.</b> Um agente que vê só o link e o repositório, como a banca, revisou o projeto duas vezes. O
              que ele achou foi corrigido e está no LOG.md.
            </li>
          </ul>
          <p className="limites">
            Limites: o ganho em R$ é estimativa de um modelo de perda, não medição; as ações são simuladas; o gabarito foi
            revisado pelo autor, não por alguém da operação. <a href={LIMITACOES}>Todas as limitações no README</a>.
          </p>
        </section>

        <section className="wrap bloco-sec" id="fila" aria-labelledby="t-fila">
          <Passo n={5} id="t-fila">A fila de hoje</Passo>
          <p className="p">
            Os casos aparecem na ordem do plano. Escolha um caso para ver a ficha, a decisão do agente e a mensagem ao cliente.
          </p>
          <div className="mesa">
            <div>
              <div className="abas" role="group" aria-label="Filtrar a fila">
                {(
                  [
                    ['todos', `Todos (${casos.length})`],
                    ['humano', `Revisão da analista (${humanos})`],
                    ['sozinho', `Decididos pelo agente (${sozinhos})`],
                  ] as const
                ).map(([k, rotulo]) => (
                  <button key={k} type="button" aria-pressed={filtro === k} onClick={() => setFiltro(k)}>
                    {rotulo}
                  </button>
                ))}
              </div>
              {pendentes > 0 && (
                <p className="nota">
                  {pendentes} casos ainda esperam o agente: o plano gratuito do Groq limita os tokens por dia. Use “Rodar o
                  agente agora” para decidir um deles ao vivo.
                </p>
              )}
              <ol className="lista">
                {visiveis.map((c) => (
                  <ItemFila key={c.order_id} c={c} ativo={c.order_id === sel} onClick={() => escolher(c.order_id)} />
                ))}
              </ol>
            </div>
            <div className="detalhe" ref={painel}>{sel && <Detalhe orderId={sel} />}</div>
          </div>
        </section>

        <Chamados chamados={chamados} numeros={numeros} />
      </main>

      <footer className="rodape wrap">
        <p>
          <b>Mesa de exceções</b> é o projeto de um candidato (Levi) para o Desafio AI-First do Gogroup. Não é um produto oficial
          do Gogroup.
        </p>
        <p>
          Passe o mouse ou toque em “Como calculamos” para ver a definição de cada número; todos vêm de scripts do repositório
          (docs/NUMEROS.md). <a href={REPO}>Código, SPEC e LOG no GitHub</a>.
        </p>
      </footer>
    </div>
  )
}

function ItemFila({ c, ativo, onClick }: { c: LinhaFila; ativo: boolean; onClick: () => void }) {
  const estado = c.pendente ? 'Espera o agente' : c.humano ? (c.regra ? REGRA[c.regra] ?? 'Revisão' : 'Revisão') : ACAO[c.acao]
  return (
    <li>
      <button
        type="button"
        className={`item${ativo ? ' ativo' : ''}${c.humano ? ' eh-humano' : ''}${c.pendente ? ' eh-pendente' : ''}`}
        onClick={onClick}
        aria-current={ativo ? 'true' : undefined}
      >
        <span className="ordem mono" aria-label={`prioridade ${c.prioridade}`}>{c.prioridade}</span>
        <span className="item-corpo">
          <span className="item-tipo">{TIPO[c.tipo] ?? c.tipo}</span>
          <span className="item-meta">
            {c.marca}, <span className="mono">{reais(c.valor, 2)}</span>
            {c.padrao ? `, ${CAUSA[c.padrao] ?? 'causa que se repete'}` : ''}
          </span>
        </span>
        <span className="selo">
          {c.humano && <span className="sr">Revisão da analista: </span>}
          {estado}
        </span>
      </button>
    </li>
  )
}

type Troca = { etapa: string; de?: string; para?: string; motivo?: string }

function Detalhe({ orderId }: { orderId: string }) {
  const [r, setR] = useState<Resultado | null>(null)
  const [rodando, setRodando] = useState(false)
  const [aviso, setAviso] = useState<string | null>(null)
  const [decisaoHumana, setDecisaoHumana] = useState<Record<string, 'aprovado' | 'rejeitado'>>({})
  const [editando, setEditando] = useState(false)
  const [texto, setTexto] = useState('')
  const controle = useRef<AbortController | null>(null)

  useEffect(() => {
    setR(null)
    setAviso(null)
    setEditando(false)
    carregar<Resultado>(`casos/${orderId}.json`).then((d) => {
      setR(d)
      setTexto(d?.decisao_modelo?.mensagem_cliente ?? '')
    })
    return () => controle.current?.abort()
  }, [orderId])

  async function rodarAoVivo() {
    controle.current?.abort()
    const ac = new AbortController()
    controle.current = ac
    const relogio = setTimeout(() => ac.abort(), TEMPO_LIMITE_MS)
    setRodando(true)
    setAviso(null)
    const gravada = 'A decisão abaixo é a gravada, de quando a fila foi processada.'
    try {
      const resp = await fetch(`/api/processar/${orderId}`, { method: 'POST', signal: ac.signal })
      const corpo = await resp.json().catch(() => ({}))
      if (!resp.ok || !corpo?.decisao_modelo) {
        setAviso(`O agente não respondeu agora (${corpo?.erro ?? `a API respondeu com erro ${resp.status}`}). ${gravada}`)
      } else {
        setR(corpo as Resultado)
        setTexto((corpo as Resultado).decisao_modelo?.mensagem_cliente ?? '')
      }
    } catch {
      setAviso(
        ac.signal.aborted
          ? `O modelo não respondeu em ${TEMPO_LIMITE_MS / 1000} segundos. ${gravada}`
          : `Não foi possível falar com a API. ${gravada}`,
      )
    } finally {
      clearTimeout(relogio)
      setRodando(false)
    }
  }

  if (!r) return <p className="nota">Carregando o caso…</p>
  const f = r.ficha
  const d = r.decisao_modelo
  const ferramentas = r.rastro.filter((p) => p.etapa === 'ferramenta')
  const trocas = r.rastro.filter((p) => p.etapa === 'troca_de_modelo') as Troca[]
  const estado = decisaoHumana[orderId]
  const causa = f.padrao_causa_raiz
  const aguardaFoto = (r.artefato as { ordem?: { situacao?: string } }).ordem?.situacao === 'aguardando a foto do cliente'

  return (
    <article aria-live="polite" aria-busy={rodando}>
      <div className="det-cabeca">
        <h3>
          {TIPO[f.excecao.tipo] ?? f.excecao.tipo}
          <span className="det-id mono" translate="no">{f.pedido.order_id}</span>
        </h3>
        <span className={`fonte fonte-${r.fonte}`}>{FONTE[r.fonte]}</span>
      </div>
      {d && (
        <p className="nota">
          Decidido pelo modelo {nomeModelo(r.modelo)} (prompt v{r.versao_prompt}).
          {trocas.map((t, i) => (
            <span key={i}> O {nomeModelo(t.de)} não respondeu ({t.motivo}); respondeu o {nomeModelo(t.para)}.</span>
          ))}
        </p>
      )}

      <dl className="ficha">
        <div><dt>Produto</dt><dd>{f.pedido.produto} ({f.pedido.marca}), <span className="mono">{reais(f.pedido.valor_pago, 2)}</span></dd></div>
        <div><dt>Situação</dt><dd>{STATUS[f.excecao.status] ?? f.excecao.status}, aberta há {f.excecao.dias_aberta} dias</dd></div>
        <div>
          <dt>Entrega</dt>
          <dd>
            {f.entrega.transportadora} para {f.entrega.cidade}/{f.entrega.uf}. Prometido para {f.entrega.data_prometida_ao_cliente};
            pelo prazo contratado, {f.entrega.prazo_correto_pelo_sla_dias_uteis}.{' '}
            {f.entrega.entregue ? `Entregue em ${f.entrega.data_entrega}.` : 'Ainda não entregue.'}
          </dd>
        </div>
        <div>
          <dt>Risco</dt>
          <dd>
            {pct(f.risco.prob_cancelamento_hoje)} de chance de cancelar hoje, {pct(f.risco.prob_cancelamento_em_5_dias_uteis)} se
            esperar 5 dias úteis. Esperar 1 dia custa <span className="mono">{reais(f.risco.custo_de_esperar_1_dia_util, 2)}</span>.
          </dd>
        </div>
        <div>
          <dt>Cliente</dt>
          <dd>
            {f.cliente.n_pedidos} pedidos, <span className="mono">{reais(f.cliente.receita_acumulada)}</span> no total
            {f.cliente.alto_valor_acima_1500 ? ' (cliente de alto valor)' : ''}
          </dd>
        </div>
        {causa && (
          <div>
            <dt>Causa</dt>
            <dd>
              Faz parte de uma causa que se repete: {CAUSA[causa.id] ?? causa.descricao}. O chamado está na seção 6.
            </dd>
          </div>
        )}
      </dl>

      {r.vai_para_humano ? (
        <div className="decisao decisao-humano">
          <p className="titulo">Aguarda a Juliana: {r.regra_aplicada ? (REGRA[r.regra_aplicada] ?? 'revisão').toLowerCase() : 'revisão'}</p>
          <p>{r.motivo_humano}</p>
          {d && <p className="nota">Proposta do agente: {ACAO[d.acao].toLowerCase()}.</p>}
          {r.regra_aplicada && <p className="regra">Regra {r.regra_aplicada} em src/agente/regras.py</p>}
        </div>
      ) : (
        <div className="decisao decisao-auto">
          <p className="titulo">{ACAO[r.acao_final]}</p>
          <p className="nota">
            {aguardaFoto
              ? 'Mensagem enviada; o reenvio sai quando a foto do cliente chegar (simulado).'
              : 'Executado pelo agente (simulado).'}
          </p>
        </div>
      )}

      {d && (
        <div className="bloco">
          <h4>Por que</h4>
          <p>{d.justificativa}</p>
          {(d.mensagem_cliente || editando) && (
            <>
              <h4>Mensagem ao cliente</h4>
              {editando ? (
                <textarea name="mensagem" autoComplete="off" value={texto} onChange={(e) => setTexto(e.target.value)} rows={6} aria-label="Editar mensagem ao cliente" />
              ) : (
                <blockquote className="mensagem">{texto || d.mensagem_cliente}</blockquote>
              )}
            </>
          )}
        </div>
      )}
      {!d && r.erro && <p className="nota">Sem decisão do modelo: {r.erro}</p>}

      {r.vai_para_humano && d && (
        <div className="botoes">
          {estado ? (
            <>
              <p className="nota">{estado === 'aprovado' ? 'Proposta aprovada' : 'Proposta rejeitada'} pela Juliana (simulado; nada foi enviado).</p>
              <button
                type="button"
                className="btn btn-linha btn-p"
                onClick={() => setDecisaoHumana(({ [orderId]: _, ...resto }) => resto)}
              >
                Desfazer
              </button>
            </>
          ) : (
            <>
              <button type="button" className="btn btn-primario btn-p" onClick={() => setDecisaoHumana({ ...decisaoHumana, [orderId]: 'aprovado' })}>
                Aprovar proposta
              </button>
              <button type="button" className="btn btn-linha btn-p" onClick={() => setEditando(!editando)}>
                {editando ? 'Fechar edição' : 'Editar mensagem'}
              </button>
              <button type="button" className="btn btn-linha btn-p" onClick={() => setDecisaoHumana({ ...decisaoHumana, [orderId]: 'rejeitado' })}>
                Rejeitar proposta
              </button>
            </>
          )}
        </div>
      )}

      <details className="rastro">
        <summary>O que o agente fez neste caso</summary>
        <ol>
          <li>Recebeu a ficha montada pelo código, com prazos em dias úteis, risco e causa.</li>
          {ferramentas.map((p, i) => (
            <li key={i}>
              Consultou <code>{String(p.nome)}</code> com {String(p.argumentos)}.
            </li>
          ))}
          <li>Devolveu a decisão em JSON{d ? `, com confiança ${d.confianca}` : ''}, validada contra o esquema.</li>
          <li>
            {r.regra_aplicada
              ? `Uma regra do código mandou o caso para a Juliana (${REGRA[r.regra_aplicada]?.toLowerCase() ?? 'revisão'}, regra ${r.regra_aplicada}).`
              : 'Nenhuma regra de revisão humana se aplicou.'}
          </li>
        </ol>
      </details>

      <div className="botoes">
        <button type="button" className="btn btn-escuro btn-p" onClick={rodarAoVivo} disabled={rodando}>
          {rodando ? 'Rodando o agente…' : 'Rodar o agente agora'}
        </button>
        {aviso && <p className="nota aviso" role="status">{aviso}</p>}
      </div>
    </article>
  )
}

function evidenciaLegivel(k: string, v: unknown): string {
  const s = String(v)
  return k === 'tipos de exceção' ? s.split(', ').map((t) => TIPO[t] ?? t).join(', ') : s
}

function Chamados({ chamados, numeros }: { chamados: Chamado[]; numeros: Numeros }) {
  if (!chamados.length) return null
  return (
    <section className="wrap bloco-sec" id="causas" aria-labelledby="t-causas">
      <Passo n={6} id="t-causas">Causas que se repetem</Passo>
      <p className="p">
        O código mede onde as exceções se concentram, comparando com os demais grupos, e o agente redige um chamado para o dono
        do processo. A Juliana aprova antes do envio. Com essas mudanças, cerca de <N n={numeros} id="N97" /> exceções por mês
        deixam de existir (<N n={numeros} id="N98" /> do time por mês, estimativa).
      </p>
      <div className="chamados">
        {chamados.map((c) => (
          <article key={c.padrao_id} className="chamado">
            <p className="dono">Para: {c.dono}</p>
            <h3>{CAUSA[c.padrao_id] ?? String(c.evidencia.grupo ?? c.titulo)}</h3>
            {c.hipotese_causa && <p>{c.hipotese_causa}</p>}
            {c.acao_proposta && (
              <p>
                <b>Proposta:</b> {c.acao_proposta}
              </p>
            )}
            {c.como_medir && <p className="medir">Como medir: {c.como_medir}</p>}
            <dl className="evidencia">
              {Object.entries(c.evidencia)
                .filter(([k, v]) => k !== 'grupo' && typeof v !== 'object')
                .sort(([a], [b]) => Number(GERAIS.has(a)) - Number(GERAIS.has(b)))
                .slice(0, 5)
                .map(([k, v]) => (
                  <div key={k}>
                    <dt>{k.replace(/_/g, ' ')}</dt>
                    <dd className={/^(R\$\s)?\d/.test(String(v)) ? 'mono' : undefined}>{evidenciaLegivel(k, v)}</dd>
                  </div>
                ))}
            </dl>
            <p className="autoria">
              {c.pendente
                ? 'Chamado ainda não redigido pelo agente.'
                : `Texto redigido pelo agente${c.modelo ? ` (${nomeModelo(c.modelo)})` : ''}; a evidência é calculada pelo código.`}
            </p>
          </article>
        ))}
      </div>
    </section>
  )
}

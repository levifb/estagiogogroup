import { useEffect, useMemo, useState } from 'react'
import type { Chamado, EvalResumo, Fila, LinhaFila, Numero, Resultado } from './tipos'
import { ACAO, FONTE, STATUS, TIPO, pct, reais } from './textos'

const REPO = 'https://github.com/levifb/estagiogogroup'
// Campos comuns a todo chamado; os específicos de cada padrão (ex.: brinde no CD2) aparecem primeiro.
const GERAIS = new Set([
  'tipos de exceção', 'exceções deste tipo no grupo', 'mesma proporção nos demais grupos',
  'vezes acima dos demais', 'exceções além do esperado', 'valor pago dos pedidos afetados',
])
const COR_DONO: Record<string, string> = {
  'TI do checkout': 'var(--yellow)',
  'Gestão de transportadoras': 'var(--cyan)',
  'Supervisão do CD': 'var(--orange)',
  'Qualidade / fornecedor': 'var(--pink)',
  Manutenção: 'var(--blue)',
  'Compras / planejamento': 'var(--ok)',
}

async function carregar<T>(arquivo: string): Promise<T | null> {
  try {
    const r = await fetch(`/data/${arquivo}`)
    return r.ok ? ((await r.json()) as T) : null
  } catch {
    return null
  }
}

type Numeros = Record<string, Numero>

function N({ n, id }: { n: Numeros; id: string }) {
  const x = n[id]
  if (!x) return <span>…</span>
  return (
    <abbr className="num" title={`${x.definicao}${x.estimativa ? ' (estimativa)' : ''}. Fonte: ${id} em docs/NUMEROS.md`}>
      {x.texto}
    </abbr>
  )
}

function Logo() {
  return (
    <a className="logo" href="#topo" aria-label="Mesa de exceções, início">
      <span className="logo-mark" aria-hidden="true">
        <svg viewBox="0 0 20 20" width="19" height="19">
          <rect x="3" y="4" width="14" height="2.6" rx="1.3" fill="#070f26" />
          <rect x="3" y="8.7" width="10" height="2.6" rx="1.3" fill="#070f26" />
          <rect x="3" y="13.4" width="6" height="2.6" rx="1.3" fill="#070f26" />
        </svg>
      </span>
      <span>
        Mesa de exceções
        <small>Operações · IA</small>
      </span>
    </a>
  )
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

  return (
    <div id="topo">
      <header className="nav">
        <div className="nav-in">
          <Logo />
          <nav className="nav-links" aria-label="Seções">
            <a href="#fila">Fila de hoje</a>
            <a href="#causas">Causas</a>
            <a href="#prova">Como sabemos</a>
          </nav>
          <span className="progresso" title="Casos da fila de hoje resolvidos pelo agente sem precisar da Juliana">
            <span className="progresso-barra" aria-hidden="true">
              <i style={{ width: `${casos.length ? (sozinhos / casos.length) * 100 : 0}%` }} />
            </span>
            <span>
              <b>{sozinhos}</b>/{casos.length || 150} resolvidos
            </span>
          </span>
          <a className="btn btn-cta btn-sm" href="#fila">
            Abrir a fila
          </a>
        </div>
      </header>

      <main>
        <section className="hero wrap">
          <div className="hero-grid">
            <div>
              <span className="chip">
                <span className="dot" aria-hidden="true" /> Agente de IA · Operações · 30/09/2026
              </span>
              <h1 className="hero-title">
                Das <N n={numeros} id="N01" /> exceções abertas, o agente escolhe as <span className="hl">150 de hoje</span>.
              </h1>
              <p className="hero-vip">
                <span>
                  Tratar na ordem certa, e não na ordem de chegada, evita <strong><N n={numeros} id="N72" /></strong> de perda
                  esperada (<N n={numeros} id="N73" />). O que é caro, sensível ou incerto vai para a Juliana, com o motivo.
                </span>
              </p>
              <p className="hero-p">
                Para cada pedido da fila, o agente lê a ficha, decide a ação (reenviar, cobrar a transportadora, falar com o
                cliente) e escreve a mensagem. Juliana é uma persona fictícia: a analista de exceções que aprova o que precisa de
                uma pessoa.
              </p>
              <div className="hero-cta">
                <a className="btn btn-cta" href="#fila">
                  Abrir a fila de hoje
                </a>
                <a className="btn btn-ghost" href={REPO}>
                  Ver o código
                </a>
              </div>
            </div>
            <Terminal casos={casos} chamados={chamados.length} />
          </div>
        </section>

        <section className="wrap" aria-label="Números de hoje">
          <div className="stats">
            <div className="stat s-ink">
              <b>
                <N n={numeros} id="N72" />
              </b>
              <span>a menos de perda esperada com o plano do agente (estimativa)</span>
            </div>
            <div className="stat s-cyan">
              <b>{sozinhos}</b>
              <span>dos {casos.length} casos de hoje resolvidos pelo agente</span>
            </div>
            <div className="stat s-orange">
              <b>{humanos}</b>
              <span>aguardam a Juliana, cada um com o motivo</span>
            </div>
            <div className="stat s-pink">
              <b>
                <N n={numeros} id="N32" />
              </b>
              <span>
                das exceções vêm de <N n={numeros} id="N30" /> causas de processo
              </span>
            </div>
          </div>
        </section>

        <section className="sec wrap">
          <div className="card-sec">
            <p className="phase">Fase 1 · Priorização</p>
            <h2>A ordem da fila vale dinheiro.</h2>
            <p className="p">
              O risco de cancelamento sobe em degraus com os dias úteis de atraso (4%, 10%, 22%, 40%). O plano trata primeiro
              quem vai subir de degrau se esperar, e deixa para depois quem já está no teto. É um problema de atribuição
              (casos × vagas de 150 por dia), resolvido de forma exata.
            </p>
            <Regua numeros={numeros} />
          </div>
        </section>

        <section className="sec wrap" id="fila">
          <div className="card-sec">
            <p className="phase">Fase 2 · Fila de hoje</p>
            <h2>150 casos, uma decisão para cada.</h2>
            <p className="p">
              Os casos aparecem na ordem do plano. Clique num caso para ver a ficha, a decisão do agente e a mensagem ao cliente.
              Os laranjas aguardam a Juliana.
            </p>
            <div className="mesa">
              <div>
                <div className="abas" role="tablist" aria-label="Filtrar a fila">
                  {(
                    [
                      ['todos', `Todos (${casos.length})`],
                      ['humano', `Aguardam a Juliana (${humanos})`],
                      ['sozinho', `Resolvidos (${sozinhos})`],
                    ] as const
                  ).map(([k, rotulo]) => (
                    <button key={k} role="tab" aria-selected={filtro === k} onClick={() => setFiltro(k)}>
                      {rotulo}
                    </button>
                  ))}
                </div>
                {pendentes > 0 && (
                  <p className="nota" style={{ marginTop: 10 }}>
                    {pendentes} casos ainda estão na fila do agente: o plano gratuito do Groq limita os tokens por dia, então a
                    fila é processada aos poucos. Use "Rodar o agente agora" para decidir um deles ao vivo.
                  </p>
                )}
                <ol className="lista">
                  {visiveis.map((c) => (
                    <ItemFila key={c.order_id} c={c} ativo={c.order_id === sel} onClick={() => setSel(c.order_id)} />
                  ))}
                </ol>
              </div>
              <div className="detalhe">{sel && <Detalhe orderId={sel} />}</div>
            </div>
          </div>
        </section>

        <Chamados chamados={chamados} numeros={numeros} />
        <Avaliacao ev={ev} />
      </main>

      <footer className="foot wrap">
        <div className="foot-in">
          <span>
            <b>Mesa de exceções</b>: projeto do Levi para o Desafio AI-First do Gogroup. Não é um produto oficial do Gogroup.
          </span>
          <a href={REPO}>Código, SPEC e LOG no GitHub</a>
        </div>
        <p className="nota" style={{ marginTop: 8, maxWidth: '78ch' }}>
          Dados sintéticos do desafio, persona fictícia e ações simuladas: nada é enviado a clientes. Passe o mouse sobre um
          número para ver a definição; todos vêm de scripts do repositório (docs/NUMEROS.md).
        </p>
      </footer>
    </div>
  )
}

function Terminal({ casos, chamados }: { casos: LinhaFila[]; chamados: number }) {
  const primeiros = casos.slice(0, 6)
  const humanos = casos.filter((c) => c.humano).length
  return (
    <div className="term" aria-label="Registro do agente processando a fila de hoje">
      <div className="term-top">
        <i style={{ background: '#ff5f57' }} />
        <i style={{ background: '#febc2e' }} />
        <i style={{ background: '#28c840' }} />
        <span>mesa.run</span>
      </div>
      <div className="term-body">
        <span className="y">$ mesa processar --dia 30/09/2026</span>
        {'\n'}
        <span className="m">› lendo 2.000 exceções abertas e o SLA de 5 transportadoras</span>
        {'\n'}
        <span className="c">› plano ótimo: 150 casos para hoje</span>
        {'\n'}
        {primeiros.map((c) => (
          <span key={c.order_id}>
            {c.pendente ? <span className="m">… </span> : c.humano ? <span className="p">! </span> : <span className="g">✓ </span>}
            {c.order_id} {(TIPO[c.tipo] ?? c.tipo).toLowerCase()} → {c.pendente ? 'na fila do agente' : ACAO[c.acao].toLowerCase()}
            {c.regra ? <span className="m"> ({c.regra})</span> : null}
            {'\n'}
          </span>
        ))}
        <span className="m">  … mais {Math.max(casos.length - primeiros.length, 0)} casos</span>
        {'\n'}
        <span className="c">› {chamados} chamados de causa raiz para revisar</span>
        {'\n'}
        <span className="y">› aguardando a Juliana em {humanos} casos</span>
      </div>
    </div>
  )
}

function Regua({ numeros }: { numeros: Numeros }) {
  const fifo = numeros.N70?.valor ?? 0
  const otim = numeros.N71?.valor ?? 0
  const max = Math.max(fifo, otim, 1)
  return (
    <figure className="regua" style={{ margin: '22px 0 0' }}>
      <figcaption className="label" style={{ margin: 0 }}>
        Perda esperada do estoque de hoje, 150 casos por dia útil (estimativa)
      </figcaption>
      <div className="regua-linha">
        <span className="regua-rotulo">Ordem de chegada (hoje)</span>
        <span className="trilho">
          <span className="barra barra-fifo" style={{ width: `${(fifo / max) * 100}%` }} />
        </span>
        <span className="regua-valor">
          <N n={numeros} id="N70" />
        </span>
      </div>
      <div className="regua-linha">
        <span className="regua-rotulo">Plano do agente</span>
        <span className="trilho">
          <span className="barra barra-otim" style={{ width: `${(otim / max) * 100}%` }} />
        </span>
        <span className="regua-valor">
          <N n={numeros} id="N71" />
        </span>
      </div>
      <div className="ganho">
        <span className="grande">
          <N n={numeros} id="N72" />
        </span>
        <span>
          a menos de perda, só mudando a ordem. O plano captura <N n={numeros} id="N74" /> do que dá para evitar sem aumentar o
          time.
        </span>
      </div>
    </figure>
  )
}

function ItemFila({ c, ativo, onClick }: { c: LinhaFila; ativo: boolean; onClick: () => void }) {
  return (
    <li>
      <button className={`item ${ativo ? 'ativo' : ''} ${c.humano ? 'eh-humano' : ''} ${c.pendente ? 'eh-pendente' : ''}`} onClick={onClick} aria-current={ativo}>
        <span className="num-tile">{c.prioridade}</span>
        <span className="item-corpo">
          <span className="item-tipo">{TIPO[c.tipo] ?? c.tipo}</span>
          <span className="item-meta">
            {c.order_id} · {c.marca} · {reais(c.valor, 2)}
            {c.padrao ? ` · ${c.padrao}` : ''}
          </span>
        </span>
        <span className="selo">{c.pendente ? 'Na fila do agente' : c.humano ? 'Aguarda a Juliana' : ACAO[c.acao]}</span>
      </button>
    </li>
  )
}

function Detalhe({ orderId }: { orderId: string }) {
  const [r, setR] = useState<Resultado | null>(null)
  const [rodando, setRodando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [decisaoHumana, setDecisaoHumana] = useState<Record<string, 'aprovado' | 'rejeitado'>>({})
  const [editando, setEditando] = useState(false)
  const [texto, setTexto] = useState('')

  useEffect(() => {
    setR(null)
    setErro(null)
    setEditando(false)
    carregar<Resultado>(`casos/${orderId}.json`).then((d) => {
      setR(d)
      setTexto(d?.decisao_modelo?.mensagem_cliente ?? '')
    })
  }, [orderId])

  async function rodarAoVivo() {
    setRodando(true)
    setErro(null)
    try {
      const resp = await fetch(`/api/processar/${orderId}`, { method: 'POST' })
      const corpo = await resp.json()
      if (!resp.ok) setErro(`${corpo.erro ?? 'O modelo não respondeu.'} A decisão abaixo é a gravada.`)
      else {
        setR(corpo as Resultado)
        setTexto((corpo as Resultado).decisao_modelo?.mensagem_cliente ?? '')
      }
    } catch {
      setErro('Não foi possível falar com a API. A decisão abaixo é a gravada.')
    } finally {
      setRodando(false)
    }
  }

  if (!r) return <p className="nota">Carregando o caso…</p>
  const f = r.ficha
  const d = r.decisao_modelo
  const ferramentas = r.rastro.filter((p) => p.etapa === 'ferramenta')
  const estado = decisaoHumana[orderId]

  return (
    <article aria-live="polite">
      <div className="det-cabeca">
        <h3>
          {TIPO[f.excecao.tipo] ?? f.excecao.tipo}
          <span className="det-id">{f.pedido.order_id}</span>
        </h3>
        <span className={`fonte fonte-${r.fonte}`}>{FONTE[r.fonte]}</span>
      </div>
      {d && (
        <p className="nota" style={{ marginTop: 6 }}>
          Modelo: {(r.modelo ?? 'openai/gpt-oss-120b').replace('openai/', '')}, prompt v{r.versao_prompt}
        </p>
      )}

      <dl className="ficha">
        <div><dt>Produto</dt><dd>{f.pedido.produto} ({f.pedido.marca}), {reais(f.pedido.valor_pago, 2)}</dd></div>
        <div><dt>Situação</dt><dd>{STATUS[f.excecao.status] ?? f.excecao.status}, aberta há {f.excecao.dias_aberta} dias</dd></div>
        <div>
          <dt>Entrega</dt>
          <dd>
            {f.entrega.transportadora} para {f.entrega.cidade}/{f.entrega.uf}. Prometido {f.entrega.data_prometida_ao_cliente};
            pelo SLA contratado, {f.entrega.prazo_correto_pelo_sla_dias_uteis}.{' '}
            {f.entrega.entregue ? `Entregue em ${f.entrega.data_entrega}.` : 'Ainda não entregue.'}
          </dd>
        </div>
        <div>
          <dt>Risco</dt>
          <dd>
            {pct(f.risco.prob_cancelamento_hoje)} de chance de cancelar hoje, {pct(f.risco.prob_cancelamento_em_5_dias_uteis)} se
            esperar 5 dias úteis. Esperar 1 dia custa {reais(f.risco.custo_de_esperar_1_dia_util, 2)}.
          </dd>
        </div>
        <div>
          <dt>Cliente</dt>
          <dd>
            {f.cliente.n_pedidos} pedidos, {reais(f.cliente.receita_acumulada)} no total
            {f.cliente.alto_valor_acima_1500 ? ' (cliente de alto valor)' : ''}
          </dd>
        </div>
        {f.padrao_causa_raiz && (
          <div><dt>Padrão</dt><dd>{f.padrao_causa_raiz.id}: {f.padrao_causa_raiz.descricao}</dd></div>
        )}
      </dl>

      {r.vai_para_humano ? (
        <div className="decisao decisao-humano">
          <p className="titulo">Aguarda a Juliana</p>
          <p>{r.motivo_humano}</p>
          {d && <p className="nota">Proposta do agente: {ACAO[d.acao].toLowerCase()}.</p>}
        </div>
      ) : (
        <div className="decisao decisao-auto">
          <p className="titulo">{ACAO[r.acao_final]}</p>
          <p className="nota">Executado pelo agente (simulado).</p>
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
                <textarea value={texto} onChange={(e) => setTexto(e.target.value)} rows={6} aria-label="Editar mensagem ao cliente" />
              ) : (
                <blockquote className="mensagem">{texto || d.mensagem_cliente}</blockquote>
              )}
            </>
          )}
        </div>
      )}
      {!d && r.erro && <p className="nota" style={{ marginTop: 12 }}>Sem decisão do modelo: {r.erro}</p>}

      {r.vai_para_humano && d && (
        <div className="botoes">
          {estado ? (
            <p className="nota">{estado === 'aprovado' ? 'Aprovado' : 'Rejeitado'} pela Juliana (simulado; nada foi enviado).</p>
          ) : (
            <>
              <button className="btn btn-cta btn-sm" onClick={() => setDecisaoHumana({ ...decisaoHumana, [orderId]: 'aprovado' })}>
                Aprovar proposta
              </button>
              <button className="btn btn-ghost btn-sm" onClick={() => setEditando(!editando)}>
                {editando ? 'Fechar edição' : 'Editar mensagem'}
              </button>
              <button className="btn btn-ghost btn-sm" onClick={() => setDecisaoHumana({ ...decisaoHumana, [orderId]: 'rejeitado' })}>
                Rejeitar
              </button>
            </>
          )}
        </div>
      )}

      <details className="rastro">
        <summary>O que o agente fez neste caso</summary>
        <ol>
          <li>Recebeu a ficha montada pelo código (prazos em dias úteis, risco, padrão).</li>
          {ferramentas.map((p, i) => (
            <li key={i}>
              Consultou <code>{String(p.nome)}</code> com {String(p.argumentos)}.
            </li>
          ))}
          <li>Devolveu a decisão em JSON{d ? `, com confiança ${d.confianca}` : ''}; o esquema foi validado.</li>
          <li>
            {r.regra_aplicada
              ? `A regra ${r.regra_aplicada} do código mandou o caso para a Juliana.`
              : 'Nenhuma regra de revisão humana se aplicou.'}
          </li>
        </ol>
      </details>

      <div className="botoes">
        <button className="btn btn-dark btn-sm" onClick={rodarAoVivo} disabled={rodando}>
          {rodando ? 'Rodando o agente…' : 'Rodar o agente agora'}
        </button>
        {erro && <p className="nota erro">{erro}</p>}
      </div>
    </article>
  )
}

function Chamados({ chamados, numeros }: { chamados: Chamado[]; numeros: Numeros }) {
  if (!chamados.length) return null
  return (
    <section className="sec wrap" id="causas">
      <div className="card-sec">
        <p className="phase">Fase 3 · Causa raiz</p>
        <h2>Metade das exceções tem dono fora da fila.</h2>
        <p className="p">
          O código mede onde as exceções se concentram, comparando com a taxa dos demais grupos, e o agente escreve um chamado
          para o dono do processo. A Juliana aprova antes do envio. Mudando esses processos, dá para evitar cerca de{' '}
          <N n={numeros} id="N97" /> exceções por mês (<N n={numeros} id="N98" /> do time).
        </p>
        <div className="chamados">
          {chamados.map((c) => (
            <article key={c.padrao_id} className="chamado" style={{ ['--c' as string]: COR_DONO[c.dono] ?? 'var(--yellow)' }}>
              <p className="dono">
                {c.padrao_id} · {c.dono}
              </p>
              <h3>{c.titulo ?? String(c.evidencia.grupo ?? c.padrao_id)}</h3>
              {c.hipotese_causa && <p>{c.hipotese_causa}</p>}
              {c.acao_proposta && (
                <p>
                  <strong>Proposta:</strong> {c.acao_proposta}
                </p>
              )}
              {c.como_medir && <p className="medir">Como medir: {c.como_medir}</p>}
              <ul className="evidencia">
                {Object.entries(c.evidencia)
                  .filter(([k, v]) => k !== 'grupo' && typeof v !== 'object')
                  .sort(([a], [b]) => Number(GERAIS.has(a)) - Number(GERAIS.has(b)))
                  .slice(0, 5)
                  .map(([k, v]) => (
                    <li key={k}>
                      <span>{k.replace(/_/g, ' ')}</span>
                      <b>{String(v)}</b>
                    </li>
                  ))}
              </ul>
              {c.pendente && <p className="medir">Chamado ainda não redigido pelo agente.</p>}
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

function Avaliacao({ ev }: { ev: EvalResumo | null }) {
  if (!ev) return null
  const s = ev.resumo
  const frac = (x: [number, number]) => `${x[0]} de ${x[1]}`
  return (
    <section className="sec wrap" id="prova">
      <div className="escuro">
        <div>
          <p className="phase" style={{ background: 'var(--yellow)', color: 'var(--ink)' }}>
            Fase 4 · Como sabemos
          </p>
          <h2>
            Medido em gabarito, <em>não no achismo</em>.
          </h2>
          <p className="p">
            {s.n} casos dos dados com a resposta certa pela política rodam contra o mesmo código desta página (eval/eval.py,
            prompt v{ev.versao_prompt}, {ev.modelo}). O LOG.md do repositório registra cada erro que a IA cometeu e como foi
            corrigido.
          </p>
          <ul className="metricas">
            <li><span>Ação certa pela política</span><b>{s.acao_aceitavel} de {s.n}</b></li>
            <li className="base"><span>Automação ingênua, sem IA (ação fixa por tipo)</span><b>{s.linha_de_base_aceitavel} de {s.n}</b></li>
            {s.tabela_politica_aceitavel !== undefined && (
              <li className="base"><span>Tabela de política em código, sem IA (o gabarito saiu dela)</span><b>{s.tabela_politica_aceitavel} de {s.n}</b></li>
            )}
            <li><span>Padrão de causa raiz identificado</span><b>{frac(s.padrao_certo)}</b></li>
            {'mensagens_sem_problema' in s && (
              <li>
                <span>Mensagens sem problema nas checagens automáticas</span>
                <b>{frac((s as unknown as { mensagens_sem_problema: [number, number] }).mensagens_sem_problema)}</b>
              </li>
            )}
            {s.json_1a_tentativa[1] > 0 && (
              <li><span>JSON válido na primeira tentativa</span><b>{frac(s.json_1a_tentativa)}</b></li>
            )}
          </ul>
        </div>
        <div className="destaque">
          <span className="grande">{frac(s.recall_humano)}</span>
          <p>casos de risco do gabarito foram para a Juliana. Esse é o erro caro: um caso de risco tratado sozinho.</p>
          <a className="btn btn-cta" href={REPO}>
            Ver o eval e o LOG
          </a>
        </div>
      </div>
    </section>
  )
}

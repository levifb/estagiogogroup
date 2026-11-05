import { useEffect, useMemo, useState } from 'react'
import type { Chamado, EvalResumo, Fila, LinhaFila, Numero, Resultado } from './tipos'
import { ACAO, FONTE, STATUS, TIPO, pct, reais } from './textos'

const REPO = 'https://github.com/levifb/estagiogogroup'

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
  if (!x) return <span>?</span>
  return (
    <abbr className="num" title={`${x.definicao}${x.estimativa ? ' (estimativa)' : ''} · ${id} em docs/NUMEROS.md`}>
      {x.texto}
    </abbr>
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
      setSel(d.casos.find((c) => c.humano)?.order_id ?? d.casos[0]?.order_id ?? null)
    })
    carregar<Chamado[]>('chamados.json').then((d) => d && setChamados(d))
    carregar<EvalResumo>('eval.json').then(setEv)
  }, [])

  const casos = fila?.casos ?? []
  const humanos = casos.filter((c) => c.humano).length
  const visiveis = useMemo(
    () => casos.filter((c) => (filtro === 'todos' ? true : filtro === 'humano' ? c.humano : !c.humano)),
    [casos, filtro],
  )

  return (
    <>
      <header className="topo">
        <div className="largura topo-linha">
          <span className="marca">Mesa de exceções</span>
          <span className="aviso">Dados sintéticos do Desafio AI-First Gogroup · referência 30/09/2026</span>
          <a href={REPO}>Código e documentação</a>
        </div>
      </header>

      <main>
        <section className="abertura largura">
          <h1>
            Marina tem <N n={numeros} id="N01" /> exceções abertas e 150 tratativas por dia.
          </h1>
          <p className="lead">
            Um agente de IA escolhe as 150 de hoje e propõe o que fazer em cada uma: reenviar, cobrar a transportadora,
            falar com o cliente. O que é caro, sensível ou incerto vai para a Marina, com o motivo. Marina é uma persona
            fictícia, analista de exceções de operações.
          </p>

          <Regua numeros={numeros} />

          <ul className="fatos">
            <li>
              <strong>{casos.length - humanos}</strong> dos {casos.length} casos de hoje resolvidos pelo agente
            </li>
            <li>
              <strong>{humanos}</strong> aguardam a Marina
            </li>
            <li>
              <strong>
                <N n={numeros} id="N32" />
              </strong>{' '}
              das exceções vêm de <N n={numeros} id="N30" /> causas de processo, e o agente abre um chamado para cada
            </li>
          </ul>
        </section>

        <section className="mesa largura" aria-label="Fila de hoje">
          <div className="fila">
            <div className="fila-cabeca">
              <h2>Fila de hoje</h2>
              <div className="abas" role="tablist">
                {(
                  [
                    ['todos', `Todos (${casos.length})`],
                    ['humano', `Aguardam a Marina (${humanos})`],
                    ['sozinho', `Resolvidos pelo agente (${casos.length - humanos})`],
                  ] as const
                ).map(([k, rotulo]) => (
                  <button key={k} role="tab" aria-selected={filtro === k} onClick={() => setFiltro(k)}>
                    {rotulo}
                  </button>
                ))}
              </div>
            </div>
            <p className="nota">
              Ordem do plano ótimo: primeiro quem mais piora se esperar mais um dia, não quem chegou antes.
            </p>
            <ol className="lista">
              {visiveis.map((c) => (
                <ItemFila key={c.order_id} c={c} ativo={c.order_id === sel} onClick={() => setSel(c.order_id)} />
              ))}
            </ol>
          </div>
          <div className="detalhe">{sel && <Detalhe orderId={sel} />}</div>
        </section>

        <Chamados chamados={chamados} />
        <Avaliacao ev={ev} numeros={numeros} />
      </main>

      <footer className="rodape largura">
        <p>
          Projeto do Levi para o Desafio AI-First do Gogroup. Os dados são os sintéticos do desafio; a persona é fictícia;
          as ações são simuladas e nada é enviado a clientes. Cada número da página tem a definição no balão e vem de um
          script do repositório (docs/NUMEROS.md).
        </p>
      </footer>
    </>
  )
}

function Regua({ numeros }: { numeros: Numeros }) {
  const fifo = numeros.N70?.valor ?? 0
  const otim = numeros.N71?.valor ?? 0
  const max = Math.max(fifo, otim, 1)
  return (
    <figure className="regua">
      <figcaption>
        Perda esperada com o estoque de hoje, tratando 150 por dia útil até zerar (reembolsos, recompras perdidas e
        reenvios; estimativa)
      </figcaption>
      <div className="regua-linha">
        <span className="regua-rotulo">Ordem de chegada (hoje)</span>
        <span className="barra barra-fifo" style={{ width: `${(fifo / max) * 100}%` }} />
        <span className="regua-valor">
          <N n={numeros} id="N70" />
        </span>
      </div>
      <div className="regua-linha">
        <span className="regua-rotulo">Plano do agente</span>
        <span className="barra barra-otim" style={{ width: `${(otim / max) * 100}%` }} />
        <span className="regua-valor">
          <N n={numeros} id="N71" />
        </span>
      </div>
      <p className="regua-ganho">
        <N n={numeros} id="N72" /> a menos de perda (<N n={numeros} id="N73" />), só mudando a ordem.
      </p>
    </figure>
  )
}

function ItemFila({ c, ativo, onClick }: { c: LinhaFila; ativo: boolean; onClick: () => void }) {
  return (
    <li>
      <button className={`item ${ativo ? 'ativo' : ''} ${c.humano ? 'eh-humano' : ''}`} onClick={onClick} aria-current={ativo}>
        <span className="item-pri">{c.prioridade}</span>
        <span className="item-corpo">
          <span className="item-tipo">{TIPO[c.tipo] ?? c.tipo}</span>
          <span className="item-meta">
            {c.order_id}, {c.marca}, {reais(c.valor, 2)}
            {c.padrao ? `, padrão ${c.padrao}` : ''}
          </span>
        </span>
        <span className="item-acao">{ACAO[c.acao]}</span>
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
      if (!resp.ok) setErro(corpo.erro ?? 'O modelo não respondeu. A decisão abaixo é a gravada.')
      else {
        setR(corpo as Resultado)
        setTexto((corpo as Resultado).decisao_modelo?.mensagem_cliente ?? '')
      }
    } catch {
      setErro('Não consegui falar com a API. A decisão abaixo é a gravada.')
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
          {TIPO[f.excecao.tipo] ?? f.excecao.tipo} <span className="det-id">{f.pedido.order_id}</span>
        </h3>
        <span className={`fonte fonte-${r.fonte}`}>{FONTE[r.fonte]}</span>
      </div>

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
        <div className="caixa caixa-humano">
          <p className="caixa-titulo">Aguarda a Marina</p>
          <p>{r.motivo_humano}</p>
          {d && <p className="nota">Proposta do agente: {ACAO[d.acao]}.</p>}
        </div>
      ) : (
        <div className="caixa caixa-auto">
          <p className="caixa-titulo">{ACAO[r.acao_final]}</p>
          <p className="nota">Executado pelo agente (simulado).</p>
        </div>
      )}

      {d && (
        <>
          <h4>Por que</h4>
          <p>{d.justificativa}</p>
          {(d.mensagem_cliente || editando) && (
            <>
              <h4>Mensagem ao cliente</h4>
              {editando ? (
                <textarea value={texto} onChange={(e) => setTexto(e.target.value)} rows={6} aria-label="Editar mensagem ao cliente" />
              ) : (
                <blockquote>{texto || d.mensagem_cliente}</blockquote>
              )}
            </>
          )}
        </>
      )}
      {!d && r.erro && <p className="nota">Sem decisão do modelo: {r.erro}</p>}

      {r.vai_para_humano && d && (
        <div className="botoes">
          {estado ? (
            <p className="nota">
              {estado === 'aprovado' ? 'Aprovado' : 'Rejeitado'} pela Marina (simulado; nada foi enviado).
            </p>
          ) : (
            <>
              <button className="primario" onClick={() => setDecisaoHumana({ ...decisaoHumana, [orderId]: 'aprovado' })}>
                Aprovar proposta
              </button>
              <button onClick={() => setEditando(!editando)}>{editando ? 'Fechar edição' : 'Editar mensagem'}</button>
              <button onClick={() => setDecisaoHumana({ ...decisaoHumana, [orderId]: 'rejeitado' })}>Rejeitar</button>
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
          <li>
            Devolveu a decisão em JSON{d ? `, com confiança ${d.confianca}` : ''}; o esquema foi validado.
          </li>
          <li>
            {r.regra_aplicada
              ? `A regra ${r.regra_aplicada} do código mandou o caso para a Marina.`
              : 'Nenhuma regra de revisão humana se aplicou.'}
          </li>
        </ol>
      </details>

      <div className="botoes">
        <button onClick={rodarAoVivo} disabled={rodando}>
          {rodando ? 'Rodando o agente…' : 'Rodar o agente agora'}
        </button>
        {erro && <p className="nota erro">{erro}</p>}
      </div>
    </article>
  )
}

function Chamados({ chamados }: { chamados: Chamado[] }) {
  if (!chamados.length) return null
  return (
    <section className="chamados largura">
      <h2>O que está causando as exceções</h2>
      <p className="lead">
        O código mede onde as exceções se concentram e o agente escreve um chamado para o dono do processo. A Marina
        aprova antes do envio.
      </p>
      <div className="grade">
        {chamados.map((c) => (
          <article key={c.padrao_id} className="chamado">
            <p className="chamado-dono">
              {c.padrao_id}, para {c.dono}
            </p>
            <h3>{c.titulo ?? String(c.evidencia.grupo ?? c.padrao_id)}</h3>
            {c.hipotese_causa && <p>{c.hipotese_causa}</p>}
            {c.acao_proposta && (
              <p>
                <strong>Proposta:</strong> {c.acao_proposta}
              </p>
            )}
            {c.como_medir && <p className="nota">Como medir: {c.como_medir}</p>}
            {c.pendente && <p className="nota">Chamado ainda não redigido pelo agente.</p>}
          </article>
        ))}
      </div>
    </section>
  )
}

function Avaliacao({ ev, numeros }: { ev: EvalResumo | null; numeros: Numeros }) {
  if (!ev) return null
  const s = ev.resumo
  const frac = (x: [number, number]) => `${x[0]} de ${x[1]}`
  return (
    <section className="avaliacao largura">
      <h2>Como sabemos que funciona</h2>
      <p className="lead">
        Um gabarito de {s.n} casos dos dados, com a resposta certa pela política, roda contra o mesmo código desta página
        (eval/eval.py, prompt v{ev.versao_prompt}, modelo {ev.modelo}).
      </p>
      <table className="tabela">
        <tbody>
          <tr><th scope="row">Casos de risco que foram para a Marina</th><td>{frac(s.recall_humano)}</td></tr>
          <tr><th scope="row">Ação certa pela política</th><td>{s.acao_aceitavel} de {s.n}</td></tr>
          <tr><th scope="row">Automação simples, sem IA (ação fixa por tipo)</th><td>{s.linha_de_base_aceitavel} de {s.n}</td></tr>
          <tr><th scope="row">Padrão de causa raiz identificado</th><td>{frac(s.padrao_certo)}</td></tr>
          <tr><th scope="row">Resposta em JSON válida na primeira tentativa</th><td>{frac(s.json_1a_tentativa)}</td></tr>
        </tbody>
      </table>
      <p className="nota">
        Mudando processos, dá para evitar cerca de <N n={numeros} id="N97" /> exceções por mês (<N n={numeros} id="N98" /> do
        time). Os erros que a IA cometeu e como foram corrigidos estão no LOG.md do repositório.
      </p>
    </section>
  )
}

export type Acao =
  | 'reenviar'
  | 'refazer_personalizacao'
  | 'reembolsar'
  | 'acionar_transportadora'
  | 'contatar_cliente'
  | 'aguardar'
  | 'escalar_humano'

export type Fonte = 'ao_vivo' | 'cache' | 'sem_modelo'

export interface LinhaFila {
  order_id: string
  prioridade: number
  tipo: string
  status: string
  marca: string
  valor: number
  perda_hoje: number
  custo_espera_1d: number
  padrao: string | null
  acao: Acao
  humano: boolean
  pendente?: boolean
  motivo_humano: string | null
  regra: string | null
  fonte: Fonte
}

export interface Fila {
  data_referencia: string
  versao_prompt: number
  casos: LinhaFila[]
}

export interface Decisao {
  acao: Acao
  justificativa: string
  mensagem_cliente: string | null
  pertence_a_padrao: string | null
  confianca: 'alta' | 'media' | 'baixa'
  precisa_humano: boolean
  motivo_humano: string | null
}

export interface PassoRastro {
  etapa: string
  [k: string]: unknown
}

export interface Resultado {
  order_id: string
  tipo_excecao: string
  fonte: Fonte
  decisao_modelo: Decisao | null
  acao_final: Acao
  vai_para_humano: boolean
  motivo_humano: string | null
  regra_aplicada: string | null
  artefato: Record<string, unknown>
  ficha: Ficha
  rastro: PassoRastro[]
  versao_prompt: number
  modelo?: string | null
  erro: string | null
}

export interface Ficha {
  pedido: { order_id: string; marca: string; produto: string; valor_pago: number; cd: string; turno: string; maquina: string | null; lote_produto: string }
  excecao: { tipo: string; status: string; aberta_em: string; dias_aberta: number; status_incoerente_com_tipo: boolean }
  entrega: {
    transportadora: string; uf: string; cidade: string; sla_contratado_dias_uteis: number
    data_prometida_ao_cliente: string; prazo_correto_pelo_sla_dias_uteis: string; entregue: boolean
    data_entrega: string | null; dias_uteis_atraso_vs_prometido: number; dias_uteis_atraso_vs_sla_contratado: number
    dentro_do_sla_contratado: boolean
  }
  cliente: { customer_id: string; n_pedidos: number; receita_acumulada: number; alto_valor_acima_1500: boolean }
  risco: { prob_cancelamento_hoje: number; prob_cancelamento_em_5_dias_uteis: number; perda_esperada_hoje: number; custo_de_esperar_1_dia_util: number }
  padrao_causa_raiz: { id: string; descricao: string; casos: number; dono: string } | null
}

export interface Numero {
  id: string
  valor: number
  texto: string
  definicao: string
  script: string
  estimativa: boolean
}

export interface Chamado {
  padrao_id: string
  dono: string
  evidencia: Record<string, unknown>
  titulo?: string
  hipotese_causa?: string
  acao_proposta?: string
  como_medir?: string
  pendente?: boolean
}

export interface EvalResumo {
  arquivo: string
  versao_prompt: number
  modelo: string
  resumo: {
    acao_aceitavel: number
    acao_exata: number
    linha_de_base_aceitavel: number
    n: number
    recall_humano: [number, number]
    precisao_humano: [number, number]
    padrao_certo: [number, number]
    padrao_falso: [number, number]
    json_1a_tentativa: [number, number]
    resolvidos_sozinhos: [number, number]
    tokens_medio: number | null
  }
}

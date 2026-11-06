import type { Acao } from './tipos'

export const ACAO: Record<Acao, string> = {
  reenviar: 'Reenviar o pedido',
  refazer_personalizacao: 'Produzir de novo',
  reembolsar: 'Reembolsar',
  acionar_transportadora: 'Cobrar a transportadora',
  contatar_cliente: 'Falar com o cliente',
  aguardar: 'Aguardar',
  escalar_humano: 'Aguarda a Juliana',
}

export const TIPO: Record<string, string> = {
  atraso_entrega: 'Atraso na entrega',
  rastreio_parado: 'Rastreio parado',
  extravio: 'Extravio',
  devolvido_transportadora: 'Devolvido pela transportadora',
  avaria_transporte: 'Avaria no transporte',
  vazamento_produto: 'Produto vazou',
  item_faltante: 'Item faltando',
  falha_personalizacao: 'Falha na personalização',
  pagamento_pendente: 'Pagamento pendente',
  endereco_divergente: 'Endereço divergente',
  ruptura_pos_venda: 'Sem estoque após a venda',
}

export const STATUS: Record<string, string> = {
  aberta: 'aberta',
  em_analise: 'em análise',
  aguardando_transportadora: 'aguardando transportadora',
  aguardando_cliente: 'aguardando cliente',
}

export const FONTE: Record<string, string> = {
  ao_vivo: 'decisão ao vivo',
  cache: 'decisão gravada',
  sem_modelo: 'sem decisão do modelo',
}

export const reais = (v: number, casas = 0) =>
  v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: casas, maximumFractionDigits: casas })

export const pct = (v: number) => `${Math.round(v * 100)}%`

// Por que um caso foi para a pessoa, em linguagem de negócio. O código da regra (src/agente/regras.py) fica como detalhe.
export const REGRA: Record<string, string> = {
  H1: 'Registro contraditório',
  H2: 'Reembolso acima do limite',
  H2b: 'Reenvio caro',
  H3: 'Cliente de alto valor',
  H4: 'Atraso longo sem entrega',
  H5: 'Fora do prazo da política',
  H6: 'O agente pediu revisão',
  H7: 'Mensagem sem pedir a foto',
}

// Nome curto de cada causa que se repete (padrões detectados em src/dados/padroes.py).
export const CAUSA: Record<string, string> = {
  P00: 'Prazo do checkout em dias corridos',
  P01: 'Rota Express no Nordeste',
  P02: 'CD2, turno da noite',
  P03: 'Avaria na Carga Norte',
  P04: 'Lote L2607-B vazando',
  P05: 'Impressora IMP-02',
  P06: 'Ruptura na Kokeshi',
}

export const nomeModelo = (m?: string | null) => (m ?? 'openai/gpt-oss-120b').replace(/^(openai|qwen)\//, '')

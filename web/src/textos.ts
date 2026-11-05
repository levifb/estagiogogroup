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

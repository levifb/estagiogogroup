"""Dias úteis e prazos, conforme dados/operacoes/parametros.md.

Regra do checkout: 1 dia útil de separação + SLA da transportadora, em dias úteis.
O dia 1 é o primeiro dia útil depois do pedido (o dia de separação). Pedido na
sexta, no sábado ou no domingo: a segunda seguinte é o dia 1.
"""

import numpy as np
import pandas as pd

FERIADOS = np.array(["2026-09-07", "2026-10-12"], dtype="datetime64[D]")


def _d(x) -> np.datetime64:
    return np.datetime64(pd.Timestamp(x).date(), "D")


def dia_separacao(data_pedido) -> pd.Timestamp:
    """Primeiro dia útil estritamente depois do pedido."""
    return pd.Timestamp(np.busday_offset(_d(data_pedido) + 1, 0, roll="forward", holidays=FERIADOS))


def prazo_correto(data_pedido, sla_dias_uteis: int) -> pd.Timestamp:
    """Prazo pela regra do parâmetro: dia de separação + SLA em dias úteis."""
    sep = np.datetime64(dia_separacao(data_pedido).date(), "D")
    return pd.Timestamp(np.busday_offset(sep, int(sla_dias_uteis), holidays=FERIADOS))


def prazo_dias_corridos(data_pedido, sla_dias_uteis: int) -> pd.Timestamp:
    """Como o sistema atual calcula data_prometida (achado: 1 + SLA em dias corridos)."""
    return pd.Timestamp(data_pedido).normalize() + pd.Timedelta(days=1 + int(sla_dias_uteis))


def dias_uteis_atraso(prazo, entrega_ou_referencia) -> int:
    """Dias úteis depois do prazo até a entrega (ou até a data de referência). 0 se no prazo.

    Suposição S-cal-1: entrega depois do prazo conta pelo menos 1 dia de atraso, mesmo que
    caia em fim de semana ou feriado (prazo sexta, entrega sábado = 1). O cliente percebe o atraso.
    """
    a, b = _d(prazo), _d(entrega_ou_referencia)
    if b <= a:
        return 0
    return max(1, int(np.busday_count(a + 1, b + 1, holidays=FERIADOS)))


def somar_dias_uteis(data, n: int) -> pd.Timestamp:
    """Data + n dias úteis (rola para o próximo dia útil se a data não for útil)."""
    return pd.Timestamp(np.busday_offset(_d(data), int(n), roll="forward", holidays=FERIADOS))

# Política de facturación y disponibilidad

Este documento es normativo. Cualquier cambio requiere identificar la regla
afectada, explicar la consecuencia y solicitar aprobación.

## 1. Datos de entrada

- `tarifa_diaria_acordada`: tarifa fijada en la reserva al crearla.
- `fecha_hora_retiro_prevista` y `fecha_hora_devolucion_prevista`.
- `fecha_hora_retiro_real` y `fecha_hora_devolucion_real`.

La tarifa vigente del vehículo **no** se usa para facturar una reserva existente.
Si la tarifa del vehículo cambia, la reserva conserva la tarifa acordada.

## 2. Cálculo de duraciones

Las duraciones se calculan en horas con `Decimal`, a partir de los segundos
transcurridos:

```
horas = Decimal(segundos_transcurridos) / Decimal(3600)
```

No se convierte un `float` a `Decimal` ni se usa `float` en ningún cálculo
monetario.

## 3. Bloques de 24 horas

Sea `h` una duración positiva en horas:

```
bloques = max(1, ceil(h / 24))
```

El redondeo es literal hacia arriba:

- 24 horas exactas → 1 bloque.
- 24 horas y 1 minuto → 2 bloques.
- Cualquier duración positiva menor o igual a 24 horas → 1 bloque.

## 4. Importe base

```
importe_base = bloques * tarifa_diaria_acordada
```

El importe base se determina según la comparación entre la devolución real y la
prevista:

| Caso | Condición | Importe base |
|------|-----------|--------------|
| Anticipada | `devolucion_real < devolucion_prevista` | Se recalcula con la duración efectiva |
| Puntual | `devolucion_real == devolucion_prevista` | Corresponde al período contratado |
| Tardía | `devolucion_real > devolucion_prevista` | Queda limitado al período contratado |

- En la devolución anticipada se usan las horas efectivamente transcurridas entre
  el retiro real y la devolución real, con mínimo de un bloque.
- En la devolución puntual y tardía se usan las horas contratadas entre el retiro
  previsto y la devolución prevista, con mínimo de un bloque.

## 5. Recargo por demora

Solo aplica en devoluciones tardías:

```
horas_demora = (devolucion_real - devolucion_prevista) / 3600
tarifa_horaria = tarifa_diaria_acordada / 24
recargo_exacto = horas_demora * tarifa_horaria
```

No se redondean las fracciones de hora. La demora se computa proporcionalmente al
tiempo exacto transcurrido, incluidos minutos y segundos.

## 6. Importe final y redondeo

```
importe_final = (importe_base + recargo_exacto) redondeado a 2 decimales
                con ROUND_HALF_UP
recargo_demora = importe_final - importe_base
```

Se redondea una sola vez, sobre el importe final, y se deriva el recargo
persistido para que se cumpla:

```
importe_final = importe_base + recargo_demora
```

En devoluciones anticipadas o puntuales, `recargo_demora = 0` e
`importe_final = importe_base`.

## 7. Validaciones de facturación

- La devolución real debe ser posterior al retiro real. Una duración cero o
  negativa es inválida.
- La tarifa acordada debe ser mayor que cero.
- El cierre debe persistir `importe_base`, `recargo_demora`, `importe_final`,
  `fecha_hora_devolucion_real` y `estado = 'finalizado'` en una transacción.
- El alquiler conserva el desglose económico; no se recalculan importes históricos
  si cambia la tarifa del vehículo.

## 8. Disponibilidad

### 8.1 Intervalos que bloquean

| Origen | Estado | Intervalo que bloquea |
|--------|--------|-----------------------|
| Reserva | `confirmada` | `[retiro_previsto, devolucion_prevista]` |
| Reserva | `cancelada` | Ninguno |
| Reserva | `completada` | Ninguno |
| Alquiler | `en_curso` | `[retiro_real, ∞)` |
| Alquiler | `finalizado` | Ninguno (histórico) |

### 8.2 Regla de solapamiento

Dos intervalos se solapan si y solo si:

```
nuevo_retiro < existente_devolucion
Y
nuevo_devolucion > existente_retiro
```

Los extremos que coinciden **no** se consideran solapamiento. Por lo tanto, se
permite que un alquiler termine exactamente cuando comienza el siguiente.

### 8.3 Sin buffer

No se implementa buffer automático entre alquileres en esta versión.

### 8.4 Inicio y cierre de alquileres

- Solo puede iniciarse un alquiler sobre una reserva `confirmada`.
- No puede haber otro alquiler `en_curso` para el mismo vehículo.
- Al iniciar, se registra `fecha_hora_retiro_real` y el alquiler queda `en_curso`.
- Al cerrar, se registra la devolución real, se calculan los importes, el alquiler
  pasa a `finalizado` y la reserva asociada pasa a `completada`, dentro de la
  misma transacción.
- Una reserva sin alquiler puede cancelarse; una reserva con alquiler no.

## 9. Decisiones abiertas

Estos puntos no forman parte de lo aprobado y deberán definirse antes de la fase
que los requiera:

- Finalidad y proveedor de la API externa (Fase 8).
- Ventana temporal permitida para cancelar una reserva confirmada.
- Si un vehículo o cliente puede modificarse mientras tiene un alquiler en curso.
- Política ante retiro real anterior o posterior al retiro previsto.

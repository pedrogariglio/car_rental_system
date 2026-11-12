# Casos de prueba

Casos acordados antes de implementar. Están implementados F-01 a F-14, D-01 a
D-10 y V-01 a V-10. **Última ejecución: 82 pruebas superadas.**

Convención monetaria: `Decimal`, dos decimales, `ROUND_HALF_UP`.
Tarifa de referencia `T = 10000.00`, salvo indicación contraria.

## 1. Facturación (Fase 1)

Archivo previsto: `tests/test_facturacion.py`.

| ID | Escenario | Entrada | Resultado esperado |
|----|-----------|---------|--------------------|
| F-01 | Devolución puntual | Contratado 48 h, real 48 h, `T=10000` | `importe_base=20000.00`, `recargo=0.00`, `final=20000.00` |
| F-02 | Devolución anticipada | Contratado 72 h, real 30 h, `T=10000` | `base=20000.00` (2 bloques), `recargo=0.00`, `final=20000.00` |
| F-03 | Anticipada con mínimo de un bloque | Contratado 24 h, real 3 h, `T=10000` | `base=10000.00`, `final=10000.00` |
| F-04 | Anticipada con 24 h exactas | Contratado 72 h, real 24 h, `T=10000` | `base=10000.00` (1 bloque) |
| F-05 | Límite 24 h + 1 min | Contratado 72 h, real 24 h 1 min, `T=10000` | `base=20000.00` (2 bloques) |
| F-06 | Demora de 2 h | Contratado 48 h, real 50 h, `T=10000` | `base=20000.00`, `recargo=833.33`, `final=20833.33` |
| F-07 | Demora fraccionaria de 30 min | Contratado 48 h, real 48 h 30 min, `T=10000` | `base=20000.00`, `recargo=208.33`, `final=20208.33` |
| F-08 | Demora de 1 min | Contratado 48 h, real 48 h 1 min, `T=10000` | `base=20000.00`, `recargo=6.94`, `final=20006.94` |
| F-09 | Tarifa congelada | Contratado 24 h puntual, acordada `10000`, vigente `12000` | `final=10000.00` (se usa la acordada) |
| F-10 | Redondeo HALF_UP | Contratado 24 h, real 25 h, `T=1000` | `base=1000.00`, `recargo=41.67`, `final=1041.67` |
| F-11 | Duración inválida | Devolución real igual al retiro real | Lanza excepción de validación |
| F-12 | Devolución anterior al retiro | Devolución real < retiro real | Lanza excepción de validación |
| F-13 | Tarifa inválida | `tarifa_diaria_acordada <= 0` | Lanza excepción de validación |
| F-14 | Invariante de cierre | Cualquier caso válido | `importe_final == importe_base + recargo_demora` |

## 2. Disponibilidad (Fase 4)

Archivo previsto: `tests/test_disponibilidad.py`.
Vehículo A, salvo indicación contraria.

| ID | Escenario | Descripción | Resultado esperado |
|----|-----------|-------------|--------------------|
| D-01 | Solapamiento con reserva confirmada | Existente 10/11 10:00 → 12/11 10:00; nueva 11/11 10:00 → 13/11 10:00 | Rechazada |
| D-02 | Extremos contiguos | Existente 10/11 10:00 → 12/11 10:00; nueva 12/11 10:00 → 14/11 10:00 | Permitida |
| D-03 | Reserva cancelada | Existente cancelada en el mismo intervalo | Permitida |
| D-04 | Reserva completada | Existente completada en el mismo intervalo | Permitida |
| D-05 | Alquiler en curso | Alquiler `en_curso` con retiro real 10/11 09:00, sin devolución; nueva reserva 10/11 10:00 | Rechazada |
| D-06 | Alquiler finalizado | Alquiler `finalizado` 10/11 09:00 → 11/11 09:00; nueva reserva 11/11 09:00 | Permitida |
| D-07 | Otro vehículo | Misma franja horaria, vehículo B | Permitida |
| D-08 | Mismo vehículo sin solape | Existente 10/11 10:00 → 12/11 10:00; nueva 15/11 10:00 → 16/11 10:00 | Permitida |
| D-09 | Cancelación libera intervalo | Cancelar reserva existente y crear una superpuesta | Permitida |
| D-10 | Comparación estricta | Nueva comienza exactamente cuando termina la existente | Permitida |

## 3. Validaciones y transacciones (Fases 3 a 5)

| ID | Escenario | Resultado esperado |
|----|-----------|--------------------|
| V-01 | Reserva con devolución prevista <= retiro previsto | Rechazada |
| V-02 | Patente duplicada | Rechazada por restricción de base de datos |
| V-03 | Documento de cliente duplicado | Rechazado por restricción de base de datos |
| V-04 | Reserva sobre vehículo en `baja` o `mantenimiento` | Rechazada |
| V-05 | Iniciar alquiler sobre reserva no `confirmada` | Rechazado |
| V-06 | Segundo alquiler para la misma reserva | Rechazado por `UNIQUE (reserva_id)` |
| V-07 | Iniciar alquiler con otro alquiler `en_curso` del mismo vehículo | Rechazado |
| V-08 | Cancelar reserva con alquiler asociado | Rechazado |
| V-09 | Fallo al crear reserva por solapamiento | Rollback: no queda ningún registro parcial |
| V-10 | Cierre de alquiler | Alquiler `finalizado`, reserva `completada`, desglose persistido, misma transacción |

## 4. Criterios de ejecución

- Las pruebas de facturación no deben importar `db` ni `interfaz`.
- Las pruebas de facturación y validaciones puras no requieren MySQL.
- Las pruebas de repositorios y transacciones usarán la base
  `DB_TEST_NAME` definida en `.env`.
- No se declarará una prueba como superada sin haber ejecutado pytest.

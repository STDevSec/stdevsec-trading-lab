# ADR-0001: Monolito modular, no microservicios

- Estado: Aceptado
- Fecha: 2026-10-29

## Contexto

La plataforma tiene varios dominios (datos, estrategias, backtesting, riesgo,
journal, analytics). Es tentador separarlos en servicios desde el inicio.

## Decisión

Empezamos con un **monolito modular**: un solo despliegue, con fronteras de
dominio explícitas (paquetes Python independientes + capas claras en la API).
No introducimos microservicios salvo que haya una necesidad real y demostrada de
escala, aislamiento o requisitos operativos.

## Consecuencias

- (+) Menos complejidad operativa, despliegue y debugging simples, transacciones
  locales, refactor de fronteras barato mientras el diseño madura.
- (+) Las fronteras ya existen como paquetes, así que extraer un servicio después
  es posible si se justifica.
- (−) Escala por proceso único al inicio; aceptable para el MVP self-hosted.

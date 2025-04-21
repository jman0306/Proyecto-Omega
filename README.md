# Proyecto-Omega

# TurboMessage

**TurboMessage** es un sistema distribuido de mensajería que simula un servidor de correos simplificado utilizando **gRPC** y **Protocol Buffers**. Permite a los usuarios registrarse, iniciar sesión, enviar, recibir, leer y eliminar correos electrónicos de manera persistente a través de una interfaz de consola.

## Características

- Registro e inicio de sesión con credenciales persistentes.
- Envío de correos entre usuarios registrados.
- Bandejas de entrada y salida con límite de 5 mensajes cada una.
- Lectura y marcado automático de correos como "leídos".
- Eliminación de correos de entrada o salida.
- Persistencia de usuarios y correos mediante archivos JSON.
- Comunicación cliente-servidor totalmente basada en **gRPC**.
- Servidor concurrente con soporte para múltiples usuarios conectados.

## Arquitectura

El sistema se compone de:

- Un archivo `.proto` que define los servicios y mensajes.
- Un servidor (`servidor.py`) que implementa la lógica del sistema.
- Un cliente (`cliente.py`) que ofrece una interfaz de consola para los usuarios.
- Archivos de persistencia (`users.json`, `mails.json`) que almacenan los datos de manera local.

## Tecnologías utilizadas

- Python 3
- gRPC + Protocol Buffers
- JSON para persistencia
- Concurrency con `ThreadPoolExecutor`

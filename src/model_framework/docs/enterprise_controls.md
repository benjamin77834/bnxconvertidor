# Controles empresariales

## 1. Log
`generated/audit.jsonl` registra cada componente, estado, duración,
execution_id y error. Es la trazabilidad técnica.

## 2. Correos
Los eventos de control son INPUT recibido, OUTPUT listo y ERROR.
En Colab se generan `.eml`; en Cloudera se configura SMTP.

## 3. Manifest
Incluye versión de framework/runtime/librerías y SHA-256 de configuración,
modelo, PMML y código generado.

## 4. Cifrado
El código generado se cifra para confidencialidad. La llave NO debe estar
en Git en producción: debe vivir en KMS/Secret Manager.

## 5. Firma
El manifest se firma con Ed25519. La operacionalización valida la firma y
los hashes antes de desplegar.

HASH = integridad
FIRMA = autenticidad
CIFRADO = confidencialidad

## 6. Cambio de código
Si operacionalización recibe otro código, modelo o configuración:
hash != aprobado -> RECHAZAR.

## 7. Switch de código real
Cada componente tiene un comentario `SWITCH POINT`. Se sustituye la
implementación demo por la librería corporativa y se conserva el contrato
`run(context) -> context`.

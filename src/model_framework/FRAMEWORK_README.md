# Framework Modelos MVP v0.3 Enterprise

MVP funcional para pasar de un modelo entregado por negocio a un paquete
estandarizado y verificable de operacionalización.

Incluye:
- componentes funcionales y catálogo de plugins;
- trazabilidad JSONL por componente;
- correos de control (archivo .eml en Colab o SMTP en empresa);
- Execution Manifest;
- SHA-256;
- cifrado del código generado;
- firma digital Ed25519;
- verificación antes de despliegue;
- puntos explícitos para sustituir código demo por librerías reales;
- arquitectura XGBoost + PMML/JPMML.

Seguridad:
HASH = integridad
FIRMA = autenticidad
ENCRIPTADO = confidencialidad

El entrenamiento no forma parte del framework. El ejemplo genera un modelo
solo para simular el artefacto que negocio ya habría entregado.

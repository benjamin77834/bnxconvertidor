# Contrato de componentes

Cada plugin implementa:

```python
class Component:
    name = "component_name"
    def run(self, context):
        return context
```

El YAML decide el orden.

Para conectar código real:

```python
catalog.register(
    "feature_engineering",
    CorporateFeatureEngineering()
)
```

El orquestador no cambia.

Componentes iniciales:
- data_validation
- preparation
- feature_engineering
- score
- evaluation
- package

El `score` demo usa XGBoost nativo solo para demostrar el flujo.
La implementación productiva recomendada carga el PMML aprobado y ejecuta
JPMML en JVM.

El PMML debe validarse contra el modelo original antes de certificarse.

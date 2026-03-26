from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier


def train_model(df):

    assembler = VectorAssembler(
        inputCols=["amount", "txn_count", "balance"],
        outputCol="features"
    )

    df = assembler.transform(df)

    model = RandomForestClassifier(
        featuresCol="features",
        labelCol="fraud_flag",
        numTrees=100
    )

    return model.fit(df)


def score_model(model, df):

    assembler = VectorAssembler(
        inputCols=["amount", "txn_count", "balance"],
        outputCol="features"
    )

    df = assembler.transform(df)

    return model.transform(df)
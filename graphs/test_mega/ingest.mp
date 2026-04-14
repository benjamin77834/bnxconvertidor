# Ingest graph — reads raw data and cleans it
NODE ReadCSV : SOURCE
NODE CleanData : TRANSFORM
NODE WriteStaging : SINK

ReadCSV -> CleanData
CleanData -> WriteStaging

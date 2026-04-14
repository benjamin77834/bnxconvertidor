# Enrich graph — joins with reference data
NODE ReadStaging : SOURCE
NODE ReadRef : SOURCE
NODE EnrichJoin : JOIN
NODE WriteEnriched : SINK

ReadStaging -> EnrichJoin
ReadRef -> EnrichJoin
EnrichJoin -> WriteEnriched

# Report graph — aggregates and writes final output
NODE ReadEnriched : SOURCE
NODE Aggregate : TRANSFORM
NODE WriteFinal : SINK

ReadEnriched -> Aggregate
Aggregate -> WriteFinal

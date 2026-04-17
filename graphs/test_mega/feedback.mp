# Feedback graph — reads report output, writes back to ingest input
NODE ReadReport : SOURCE
NODE ComputeDelta : TRANSFORM
NODE WriteFeedback : SINK

ReadReport -> ComputeDelta
ComputeDelta -> WriteFeedback

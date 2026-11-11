@
{18|Type|XXGrepository|Primary_Name|XXGgraph|_ab_object_schema|0|_ab_semantic_schema|21|eme_flatten_format|1|schema_version|34|root_id|0|ent_count|12|rel_count|12|}
{2010001002|XXGdirectory|0|1|1|0|{@{}@}}
{2010600005|XXGgraph|1|0|1|0|{Ejercicio: score y reporte de riesgo|}@0|@10000|442500|0|0|0|0|1|Data|}}
{30001002|XXparameter|FECHA_PROCESO|20250115|3|2|$|@{0|}}
{30001002|XXparameter|UMBRAL_ALERTA|60|3|2|$|@{0|}}
{2010503005|XXGfvertex|10|0|256|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|9|Pf|@{0|}}
{30001002|XXparameter|Layout|/banca/resumen_cliente_diario.dat|3|2|$|@{0|}}
{30001002|XXparameter|metadata_file|$AI_DML/resumen_cliente.dml|3|2|$|@{0|}}
{30001002|XXparameter|out_metadata|record
  string(10) id_cliente;
  string(40) nombre;
  string(8) nivel_cliente;
  decimal(12,2) limite_credito;
  decimal(14,2) total_monto;
  integer(4) num_tx;
end;|3|2|$|@{0|}}
}}@Resumen_In|@@{0|}}}
{2010501005|XXGpvertex|11|0|257|0|{Changes the record format of your data by dropping fields, or by using DML expressions to add fields, combine fields, or transform the data in the records.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|9|Pf|@{0|}}
{30001002|XXparameter|mpname|reformat|3|1|Hl||{0|}}
{30001002|XXparameter|transform_file|$AI_XFR/calcula_score.xfr|3|2|$|@{0|}}
{30001002|XXparameter|transform0|out :: reformat(in) =
begin
  out.id_cliente :: in.id_cliente;
  out.nombre :: in.nombre;
  out.total_monto :: in.total_monto;
  out.num_tx :: in.num_tx;
  out.score_riesgo :: if (in.limite_credito > 0) (in.total_monto * 100) / in.limite_credito else 100;
  out.nivel_riesgo :: if (in.total_monto > in.limite_credito) "ALTO" else "NORMAL";
end;|3|2|$|@{0|}}
}}@Calcula_Score|@@{0|}}}
{2010501005|XXGpvertex|12|0|258|0|{Filters data records according to a DML expression.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Filter_by_Expression.mpc|3|9|Pf|@{0|}}
{30001002|XXparameter|mpname|filter-by-expression|3|1|Hl||{0|}}
{30001002|XXparameter|select_expr|score_riesgo >= 60|3|2|$|@{0|}}
}}@Solo_Alertas|@@{0|}}}
{2010503005|XXGfvertex|13|0|259|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|9|Pf|@{0|}}
{30001002|XXparameter|Layout|/banca/reporte_riesgo.dat|3|2|$|@{0|}}
{30001002|XXparameter|metadata_file|$AI_DML/reporte_riesgo.dml|3|2|$|@{0|}}
{30001002|XXparameter|in_metadata|record
  string(10) id_cliente;
  string(40) nombre;
  decimal(14,2) total_monto;
  integer(4) num_tx;
  integer(4) score_riesgo;
  string(8) nivel_riesgo;
end;|3|2|$|@{0|}}
}}@Reporte_Riesgo|@@{0|}}}
{2010601001|XXGgraph_vertex_vertex|260|0|261|0|{Resumen_In|}1|10|}
{2010601001|XXGgraph_vertex_vertex|262|0|263|0|{Calcula_Score|}1|11|}
{2010601001|XXGgraph_vertex_vertex|264|0|265|0|{Solo_Alertas|}1|12|}
{2010601001|XXGgraph_vertex_vertex|266|0|267|0|{Reporte_Riesgo|}1|13|}
{2010212001|XXGvertex_oport_oport|268|0|269|0|{0|out|}10|1000|}
{2010211001|XXGvertex_iport_iport|270|0|271|0|{0|in0|}11|1001|}
{2010213001|XXGoport_dst_flow|272|0|273|0|{0|}1000|1002|}
{2010214001|XXGiport_src_flow|274|0|275|0|{0|}1001|1002|}
{2010212001|XXGvertex_oport_oport|276|0|277|0|{0|out|}11|1010|}
{2010211001|XXGvertex_iport_iport|278|0|279|0|{0|in0|}12|1011|}
{2010213001|XXGoport_dst_flow|280|0|281|0|{0|}1010|1012|}
{2010214001|XXGiport_src_flow|282|0|283|0|{0|}1011|1012|}
{2010212001|XXGvertex_oport_oport|284|0|285|0|{0|out|}12|1020|}
{2010211001|XXGvertex_iport_iport|286|0|287|0|{0|in0|}13|1021|}
{2010213001|XXGoport_dst_flow|288|0|289|0|{0|}1020|1022|}
{2010214001|XXGiport_src_flow|290|0|291|0|{0|}1021|1022|}

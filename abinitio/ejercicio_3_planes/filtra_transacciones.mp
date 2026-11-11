@
{18|Type|XXGrepository|Primary_Name|XXGgraph|_ab_object_schema|0|_ab_semantic_schema|21|eme_flatten_format|1|schema_version|34|root_id|0|ent_count|12|rel_count|12|}
{2010001002|XXGdirectory|0|1|1|0|{@{}@}}
{2010600005|XXGgraph|1|0|1|0|{Ejercicio: filtra transacciones validas|}@0|@10000|442500|0|0|0|0|1|Data|}}
{30001002|XXparameter|FECHA_PROCESO|20250115|3|2|$|@{0|}}
{30001002|XXparameter|MONTO_MINIMO|0|3|2|$|@{0|}}
{2010503005|XXGfvertex|10|0|173|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|9|Pf|@{0|}}
{30001002|XXparameter|Layout|/banca/transacciones_raw.dat|3|2|$|@{0|}}
{30001002|XXparameter|metadata_file|$AI_DML/transacciones.dml|3|2|$|@{0|}}
{30001002|XXparameter|out_metadata|record
  string(12) id_tx;
  string(10) id_cliente;
  string(10) fecha_tx;
  string(10) tipo_tx;
  decimal(12,2) monto;
  string(2) estatus;
end;|3|2|$|@{0|}}
}}@Transacciones_Raw|@@{0|}}}
{2010501005|XXGpvertex|11|0|174|0|{Filters data records according to a DML expression.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Filter_by_Expression.mpc|3|9|Pf|@{0|}}
{30001002|XXparameter|mpname|filter-by-expression|3|1|Hl||{0|}}
{30001002|XXparameter|select_expr|estatus == "OK" && monto > 0|3|2|$|@{0|}}
}}@Solo_Validas|@@{0|}}}
{2010501005|XXGpvertex|12|0|175|0|{Changes the record format of your data by dropping fields, or by using DML expressions to add fields, combine fields, or transform the data in the records.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|9|Pf|@{0|}}
{30001002|XXparameter|mpname|reformat|3|1|Hl||{0|}}
{30001002|XXparameter|transform_file|$AI_XFR/normaliza_tx.xfr|3|2|$|@{0|}}
{30001002|XXparameter|transform0|out :: reformat(in) =
begin
  out.id_tx :: in.id_tx;
  out.id_cliente :: string_lrtrim(in.id_cliente);
  out.fecha_tx :: in.fecha_tx;
  out.tipo_tx :: string_upcase(in.tipo_tx);
  out.monto :: in.monto;
  out.estatus :: in.estatus;
end;|3|2|$|@{0|}}
}}@Normaliza_Tx|@@{0|}}}
{2010503005|XXGfvertex|13|0|176|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|9|Pf|@{0|}}
{30001002|XXparameter|Layout|/banca/transacciones_validas.dat|3|2|$|@{0|}}
{30001002|XXparameter|metadata_file|$AI_DML/transacciones.dml|3|2|$|@{0|}}
{30001002|XXparameter|in_metadata|record
  string(12) id_tx;
  string(10) id_cliente;
  string(10) fecha_tx;
  string(10) tipo_tx;
  decimal(12,2) monto;
  string(2) estatus;
end;|3|2|$|@{0|}}
}}@Transacciones_Validas|@@{0|}}}
{2010601001|XXGgraph_vertex_vertex|177|0|178|0|{Transacciones_Raw|}1|10|}
{2010601001|XXGgraph_vertex_vertex|179|0|180|0|{Solo_Validas|}1|11|}
{2010601001|XXGgraph_vertex_vertex|181|0|182|0|{Normaliza_Tx|}1|12|}
{2010601001|XXGgraph_vertex_vertex|183|0|184|0|{Transacciones_Validas|}1|13|}
{2010212001|XXGvertex_oport_oport|185|0|186|0|{0|out|}10|1000|}
{2010211001|XXGvertex_iport_iport|187|0|188|0|{0|in0|}11|1001|}
{2010213001|XXGoport_dst_flow|189|0|190|0|{0|}1000|1002|}
{2010214001|XXGiport_src_flow|191|0|192|0|{0|}1001|1002|}
{2010212001|XXGvertex_oport_oport|193|0|194|0|{0|out|}11|1010|}
{2010211001|XXGvertex_iport_iport|195|0|196|0|{0|in0|}12|1011|}
{2010213001|XXGoport_dst_flow|197|0|198|0|{0|}1010|1012|}
{2010214001|XXGiport_src_flow|199|0|200|0|{0|}1011|1012|}
{2010212001|XXGvertex_oport_oport|201|0|202|0|{0|out|}12|1020|}
{2010211001|XXGvertex_iport_iport|203|0|204|0|{0|in0|}13|1021|}
{2010213001|XXGoport_dst_flow|205|0|206|0|{0|}1020|1022|}
{2010214001|XXGiport_src_flow|207|0|208|0|{0|}1021|1022|}

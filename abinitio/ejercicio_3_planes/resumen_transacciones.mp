@
{18|Type|XXGrepository|Primary_Name|XXGgraph|_ab_object_schema|0|_ab_semantic_schema|21|eme_flatten_format|1|schema_version|34|root_id|0|ent_count|15|rel_count|16|}
{2010001002|XXGdirectory|0|1|1|0|{@{}@}}
{2010600005|XXGgraph|1|0|1|0|{Ejercicio: agrega transacciones y cruza con clientes|}@0|@10000|442500|0|0|0|0|1|Data|}}
{30001002|XXparameter|FECHA_PROCESO|20250115|3|2|$|@{0|}}
{2010503005|XXGfvertex|10|0|209|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|9|Pf|@{0|}}
{30001002|XXparameter|Layout|/banca/transacciones_validas.dat|3|2|$|@{0|}}
{30001002|XXparameter|metadata_file|$AI_DML/transacciones.dml|3|2|$|@{0|}}
{30001002|XXparameter|out_metadata|record
  string(12) id_tx;
  string(10) id_cliente;
  string(10) fecha_tx;
  string(10) tipo_tx;
  decimal(12,2) monto;
  string(2) estatus;
end;|3|2|$|@{0|}}
}}@Tx_Validas_In|@@{0|}}}
{2010501005|XXGpvertex|11|0|210|0|{Generates data records that summarize groups of data records.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Rollup.mpc|3|9|Pf|@{0|}}
{30001002|XXparameter|mpname|rollup|3|1|Hl||{0|}}
{30001002|XXparameter|transform_file|$AI_XFR/suma_por_cliente.xfr|3|2|$|@{0|}}
{30001002|XXparameter|transform0|out :: rollup(in) =
begin
  out.id_cliente :: in.id_cliente;
  out.total_monto :: sum(in.monto);
  out.num_tx :: count(in.id_tx);
end;|3|2|$|@{0|}}
{30001002|XXparameter|key|\{id_cliente\}|3|2|$|@{0|}}
}}@Suma_Por_Cliente|@@{0|}}}
{2010503005|XXGfvertex|12|0|211|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|9|Pf|@{0|}}
{30001002|XXparameter|Layout|/banca/clientes_segmentados.dat|3|2|$|@{0|}}
{30001002|XXparameter|metadata_file|$AI_DML/clientes_segmentados.dml|3|2|$|@{0|}}
{30001002|XXparameter|out_metadata|record
  string(10) id_cliente;
  string(40) nombre;
  string(12) segmento;
  string(10) fecha_alta;
  decimal(12,2) limite_credito;
  string(8) nivel_cliente;
end;|3|2|$|@{0|}}
}}@Clientes_Seg_In|@@{0|}}}
{2010501005|XXGpvertex|13|0|212|0|{Joins data records from two or more input flows.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Join.mpc|3|9|Pf|@{0|}}
{30001002|XXparameter|mpname|join|3|1|Hl||{0|}}
{30001002|XXparameter|transform_file|$AI_XFR/cruza_clientes.xfr|3|2|$|@{0|}}
{30001002|XXparameter|transform0|out :: join(in0, in1) =
begin
  out.id_cliente :: in0.id_cliente;
  out.nombre :: in1.nombre;
  out.nivel_cliente :: in1.nivel_cliente;
  out.limite_credito :: in1.limite_credito;
  out.total_monto :: in0.total_monto;
  out.num_tx :: in0.num_tx;
end;|3|2|$|@{0|}}
{30001002|XXparameter|key|\{id_cliente\}|3|2|$|@{0|}}
}}@Cruza_Con_Clientes|@@{0|}}}
{2010503005|XXGfvertex|14|0|213|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|9|Pf|@{0|}}
{30001002|XXparameter|Layout|/banca/resumen_cliente_diario.dat|3|2|$|@{0|}}
{30001002|XXparameter|metadata_file|$AI_DML/resumen_cliente.dml|3|2|$|@{0|}}
{30001002|XXparameter|in_metadata|record
  string(10) id_cliente;
  string(40) nombre;
  string(8) nivel_cliente;
  decimal(12,2) limite_credito;
  decimal(14,2) total_monto;
  integer(4) num_tx;
end;|3|2|$|@{0|}}
}}@Resumen_Cliente_Diario|@@{0|}}}
{2010601001|XXGgraph_vertex_vertex|214|0|215|0|{Tx_Validas_In|}1|10|}
{2010601001|XXGgraph_vertex_vertex|216|0|217|0|{Suma_Por_Cliente|}1|11|}
{2010601001|XXGgraph_vertex_vertex|218|0|219|0|{Clientes_Seg_In|}1|12|}
{2010601001|XXGgraph_vertex_vertex|220|0|221|0|{Cruza_Con_Clientes|}1|13|}
{2010601001|XXGgraph_vertex_vertex|222|0|223|0|{Resumen_Cliente_Diario|}1|14|}
{2010212001|XXGvertex_oport_oport|224|0|225|0|{0|out|}10|1000|}
{2010211001|XXGvertex_iport_iport|226|0|227|0|{0|in0|}11|1001|}
{2010213001|XXGoport_dst_flow|228|0|229|0|{0|}1000|1002|}
{2010214001|XXGiport_src_flow|230|0|231|0|{0|}1001|1002|}
{2010212001|XXGvertex_oport_oport|232|0|233|0|{0|out|}11|1010|}
{2010211001|XXGvertex_iport_iport|234|0|235|0|{0|in0|}13|1011|}
{2010213001|XXGoport_dst_flow|236|0|237|0|{0|}1010|1012|}
{2010214001|XXGiport_src_flow|238|0|239|0|{0|}1011|1012|}
{2010212001|XXGvertex_oport_oport|240|0|241|0|{0|out|}12|1020|}
{2010211001|XXGvertex_iport_iport|242|0|243|0|{1|in1|}13|1021|}
{2010213001|XXGoport_dst_flow|244|0|245|0|{0|}1020|1022|}
{2010214001|XXGiport_src_flow|246|0|247|0|{1|}1021|1022|}
{2010212001|XXGvertex_oport_oport|248|0|249|0|{0|out|}13|1030|}
{2010211001|XXGvertex_iport_iport|250|0|251|0|{0|in0|}14|1031|}
{2010213001|XXGoport_dst_flow|252|0|253|0|{0|}1030|1032|}
{2010214001|XXGiport_src_flow|254|0|255|0|{0|}1031|1032|}

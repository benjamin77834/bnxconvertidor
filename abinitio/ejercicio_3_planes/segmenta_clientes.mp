@
{18|Type|XXGrepository|Primary_Name|XXGgraph|_ab_object_schema|0|_ab_semantic_schema|21|eme_flatten_format|1|schema_version|34|root_id|0|ent_count|9|rel_count|8|}
{2010001002|XXGdirectory|0|1|1|0|{@{}@}}
{2010600005|XXGgraph|1|0|1|0|{Ejercicio: segmenta clientes por limite de credito|}@0|@10000|442500|0|0|0|0|1|Data|}}
{30001002|XXparameter|FECHA_PROCESO|20250115|3|2|$|@{0|}}
{30001002|XXparameter|LIMITE_PREMIUM|50000|3|2|$|@{0|}}
{2010503005|XXGfvertex|10|0|148|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|9|Pf|@{0|}}
{30001002|XXparameter|Layout|/banca/clientes_limpios.dat|3|2|$|@{0|}}
{30001002|XXparameter|metadata_file|$AI_DML/clientes_limpios.dml|3|2|$|@{0|}}
{30001002|XXparameter|out_metadata|record
  string(10) id_cliente;
  string(40) nombre;
  string(12) segmento;
  string(1) estatus;
  string(10) fecha_alta;
  decimal(12,2) limite_credito;
end;|3|2|$|@{0|}}
}}@Clientes_Limpios_In|@@{0|}}}
{2010501005|XXGpvertex|11|0|149|0|{Changes the record format of your data by dropping fields, or by using DML expressions to add fields, combine fields, or transform the data in the records.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|9|Pf|@{0|}}
{30001002|XXparameter|mpname|reformat|3|1|Hl||{0|}}
{30001002|XXparameter|transform_file|$AI_XFR/asigna_nivel.xfr|3|2|$|@{0|}}
{30001002|XXparameter|transform0|out :: reformat(in) =
begin
  out.id_cliente :: in.id_cliente;
  out.nombre :: in.nombre;
  out.segmento :: in.segmento;
  out.fecha_alta :: in.fecha_alta;
  out.limite_credito :: in.limite_credito;
  out.nivel_cliente :: if (in.limite_credito >= 50000) "PREMIUM" else "ESTANDAR";
end;|3|2|$|@{0|}}
}}@Asigna_Nivel|@@{0|}}}
{2010503005|XXGfvertex|12|0|150|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|9|Pf|@{0|}}
{30001002|XXparameter|Layout|/banca/clientes_segmentados.dat|3|2|$|@{0|}}
{30001002|XXparameter|metadata_file|$AI_DML/clientes_segmentados.dml|3|2|$|@{0|}}
{30001002|XXparameter|in_metadata|record
  string(10) id_cliente;
  string(40) nombre;
  string(12) segmento;
  string(10) fecha_alta;
  decimal(12,2) limite_credito;
  string(8) nivel_cliente;
end;|3|2|$|@{0|}}
}}@Clientes_Segmentados|@@{0|}}}
{2010601001|XXGgraph_vertex_vertex|151|0|152|0|{Clientes_Limpios_In|}1|10|}
{2010601001|XXGgraph_vertex_vertex|153|0|154|0|{Asigna_Nivel|}1|11|}
{2010601001|XXGgraph_vertex_vertex|155|0|156|0|{Clientes_Segmentados|}1|12|}
{2010212001|XXGvertex_oport_oport|157|0|158|0|{0|out|}10|1000|}
{2010211001|XXGvertex_iport_iport|159|0|160|0|{0|in0|}11|1001|}
{2010213001|XXGoport_dst_flow|161|0|162|0|{0|}1000|1002|}
{2010214001|XXGiport_src_flow|163|0|164|0|{0|}1001|1002|}
{2010212001|XXGvertex_oport_oport|165|0|166|0|{0|out|}11|1010|}
{2010211001|XXGvertex_iport_iport|167|0|168|0|{0|in0|}12|1011|}
{2010213001|XXGoport_dst_flow|169|0|170|0|{0|}1010|1012|}
{2010214001|XXGiport_src_flow|171|0|172|0|{0|}1011|1012|}

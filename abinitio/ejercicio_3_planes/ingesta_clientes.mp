@
{18|Type|XXGrepository|Primary_Name|XXGgraph|_ab_object_schema|0|_ab_semantic_schema|21|eme_flatten_format|1|schema_version|34|root_id|0|ent_count|15|rel_count|16|}
{2010001002|XXGdirectory|0|1|1|0|{@{}@}}
{2010600005|XXGgraph|1|0|1|0|{Ejercicio: carga y limpia clientes|}@0|@10000|442500|0|0|0|0|1|Data|}}
{30001002|XXparameter|FECHA_PROCESO|20250115|3|2|$|@{0|}}
{30001002|XXparameter|RUTA_BASE|/data/banca|3|2|$|@{0|}}
{2010503005|XXGfvertex|10|0|101|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|9|Pf|@{0|}}
{30001002|XXparameter|Layout|/banca/clientes_raw.dat|3|2|$|@{0|}}
{30001002|XXparameter|metadata_file|$AI_DML/clientes_raw.dml|3|2|$|@{0|}}
{30001002|XXparameter|out_metadata|record
  string(10) id_cliente;
  string(40) nombre;
  string(12) segmento;
  string(1) estatus;
  string(10) fecha_alta;
  decimal(12,2) limite_credito;
end;|3|2|$|@{0|}}
}}@Clientes_Raw|@@{0|}}}
{2010501005|XXGpvertex|11|0|102|0|{Changes the record format of your data by dropping fields, or by using DML expressions to add fields, combine fields, or transform the data in the records.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|9|Pf|@{0|}}
{30001002|XXparameter|mpname|reformat|3|1|Hl||{0|}}
{30001002|XXparameter|transform_file|$AI_XFR/limpia_clientes.xfr|3|2|$|@{0|}}
{30001002|XXparameter|transform0|out :: reformat(in) =
begin
  out.id_cliente :: string_lrtrim(in.id_cliente);
  out.nombre :: string_upcase(string_lrtrim(in.nombre));
  out.segmento :: string_upcase(in.segmento);
  out.estatus :: in.estatus;
  out.fecha_alta :: in.fecha_alta;
  out.limite_credito :: in.limite_credito;
end;|3|2|$|@{0|}}
}}@Limpia_Clientes|@@{0|}}}
{2010501005|XXGpvertex|12|0|103|0|{Filters data records according to a DML expression.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Filter_by_Expression.mpc|3|9|Pf|@{0|}}
{30001002|XXparameter|mpname|filter-by-expression|3|1|Hl||{0|}}
{30001002|XXparameter|select_expr|estatus == "A" && limite_credito >= 0|3|2|$|@{0|}}
}}@Solo_Activos|@@{0|}}}
{2010501005|XXGpvertex|13|0|104|0|{Separates one specified data record in each group of data records from the rest of the records in the group.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Dedup_Sorted.mpc|3|9|Pf|@{0|}}
{30001002|XXparameter|mpname|dedup-sorted|3|1|Hl||{0|}}
{30001002|XXparameter|key|\{id_cliente\}|3|2|$|@{0|}}
}}@Dedup_Cliente|@@{0|}}}
{2010503005|XXGfvertex|14|0|105|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|9|Pf|@{0|}}
{30001002|XXparameter|Layout|/banca/clientes_limpios.dat|3|2|$|@{0|}}
{30001002|XXparameter|metadata_file|$AI_DML/clientes_limpios.dml|3|2|$|@{0|}}
{30001002|XXparameter|in_metadata|record
  string(10) id_cliente;
  string(40) nombre;
  string(12) segmento;
  string(1) estatus;
  string(10) fecha_alta;
  decimal(12,2) limite_credito;
end;|3|2|$|@{0|}}
}}@Clientes_Limpios|@@{0|}}}
{2010601001|XXGgraph_vertex_vertex|106|0|107|0|{Clientes_Raw|}1|10|}
{2010601001|XXGgraph_vertex_vertex|108|0|109|0|{Limpia_Clientes|}1|11|}
{2010601001|XXGgraph_vertex_vertex|110|0|111|0|{Solo_Activos|}1|12|}
{2010601001|XXGgraph_vertex_vertex|112|0|113|0|{Dedup_Cliente|}1|13|}
{2010601001|XXGgraph_vertex_vertex|114|0|115|0|{Clientes_Limpios|}1|14|}
{2010212001|XXGvertex_oport_oport|116|0|117|0|{0|out|}10|1000|}
{2010211001|XXGvertex_iport_iport|118|0|119|0|{0|in0|}11|1001|}
{2010213001|XXGoport_dst_flow|120|0|121|0|{0|}1000|1002|}
{2010214001|XXGiport_src_flow|122|0|123|0|{0|}1001|1002|}
{2010212001|XXGvertex_oport_oport|124|0|125|0|{0|out|}11|1010|}
{2010211001|XXGvertex_iport_iport|126|0|127|0|{0|in0|}12|1011|}
{2010213001|XXGoport_dst_flow|128|0|129|0|{0|}1010|1012|}
{2010214001|XXGiport_src_flow|130|0|131|0|{0|}1011|1012|}
{2010212001|XXGvertex_oport_oport|132|0|133|0|{0|out|}12|1020|}
{2010211001|XXGvertex_iport_iport|134|0|135|0|{0|in0|}13|1021|}
{2010213001|XXGoport_dst_flow|136|0|137|0|{0|}1020|1022|}
{2010214001|XXGiport_src_flow|138|0|139|0|{0|}1021|1022|}
{2010212001|XXGvertex_oport_oport|140|0|141|0|{0|out|}13|1030|}
{2010211001|XXGvertex_iport_iport|142|0|143|0|{0|in0|}14|1031|}
{2010213001|XXGoport_dst_flow|144|0|145|0|{0|}1030|1032|}
{2010214001|XXGiport_src_flow|146|0|147|0|{0|}1031|1032|}

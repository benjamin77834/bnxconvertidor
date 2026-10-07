@
{18|Type|XXGrepository|Primary_Name|XXGgraph|_ab_object_schema|0|}}
{2010600005|XXGgraph|1|0|1|0|{||}}@|@0|0|0|0|0|0|0|0|A_DRI_ECMS_AMBS_IMR_D.plan|}}
{2010703001|XXGgraphinfo|2|0|3|0|{@{}@1|4.0.2.4|{1|1|}Job 'A_DRI_ECMS_AMBS_IMR_D'}}

# ---- ROOT GRAPH vertices (XXGgraph_vertex_vertex): NAME|}PARENT|VID| ----
# Reales del grafo: 2 sources, 2 sorts, 1 join, 1 output file
{2010601001|XXGgraph_vertex_vertex|50|0|100|0|{ECMS_AMBS_D|}1|30|}
{2010601001|XXGgraph_vertex_vertex|51|0|101|0|{Sort|}1|31|}
{2010601001|XXGgraph_vertex_vertex|52|0|102|0|{ECMS_AMBSX_D|}1|32|}
{2010601001|XXGgraph_vertex_vertex|53|0|103|0|{Sort_1|}1|33|}
{2010601001|XXGgraph_vertex_vertex|54|0|104|0|{Join|}1|34|}
{2010601001|XXGgraph_vertex_vertex|55|0|105|0|{Output_File|}1|35|}

# ---- SUBGRAPH container "Graph4" (vid=40), parent is root(1) ----
{2010601001|XXGgraph_vertex_vertex|56|0|106|0|{Graph4|}1|40|}
{2010600005|XXGgraph|40|0|21|0|{Subgraph created from graph "Graph4"|}@0|@10000|442500|0|0|0|0|186|Data|}}

# ---- Children of Graph4 (parent=40): internal template plumbing ----
{2010601001|XXGgraph_vertex_vertex|60|0|110|0|{Reformat|}40|60|}
{2010601001|XXGgraph_vertex_vertex|61|0|111|0|{Redefine_Format|}40|61|}
{2010601001|XXGgraph_vertex_vertex|62|0|112|0|{Filter_by_Expression|}40|62|}
{2010601001|XXGgraph_vertex_vertex|63|0|113|0|{Dedup_Sorted|}40|63|}
{2010601001|XXGgraph_vertex_vertex|64|0|114|0|{Trash_1|}40|64|}
{2010601001|XXGgraph_vertex_vertex|65|0|115|0|{Redefine_Format_1|}40|65|}

# ================= PORTS for root chain =================
# ECMS_AMBS_D(30) out -> Sort(31) in -> Join(34) in0
{2010212001|XXGvertex_oport|200|0|300|0|{0|out|}30|500|}
{2010211001|XXGvertex_iport|201|0|301|0|{0|in|}31|501|}
{2010212001|XXGvertex_oport|202|0|302|0|{0|out|}31|502|}
{2010211001|XXGvertex_iport|203|0|303|0|{0|in0|}34|503|}
# ECMS_AMBSX_D(32) out -> Sort_1(33) in -> Join(34) in1
{2010212001|XXGvertex_oport|204|0|304|0|{0|out|}32|504|}
{2010211001|XXGvertex_iport|205|0|305|0|{0|in|}33|505|}
{2010212001|XXGvertex_oport|206|0|306|0|{0|out|}33|506|}
{2010211001|XXGvertex_iport|207|0|307|0|{1|in1|}34|507|}
# Join(34) out -> Output_File(35) in
{2010212001|XXGvertex_oport|208|0|308|0|{0|out|}34|508|}
{2010211001|XXGvertex_iport|209|0|309|0|{0|in|}35|509|}

# ================= FLOWS for root chain (oport->flow->iport) =================
# flow 600: 500 -> 501
{2010213001|XXGoport_dst_flow|300|0|400|0|{0|}500|600|}
{2010214001|XXGiport_src_flow|301|0|401|0|{0|}501|600|}
# flow 601: 502 -> 503 (Sort -> Join in0)
{2010213001|XXGoport_dst_flow|302|0|402|0|{0|}502|601|}
{2010214001|XXGiport_src_flow|303|0|403|0|{0|}503|601|}
# flow 602: 504 -> 505
{2010213001|XXGoport_dst_flow|304|0|404|0|{0|}504|602|}
{2010214001|XXGiport_src_flow|305|0|405|0|{0|}505|602|}
# flow 603: 506 -> 507 (Sort_1 -> Join in1)
{2010213001|XXGoport_dst_flow|306|0|406|0|{0|}506|603|}
{2010214001|XXGiport_src_flow|307|0|407|0|{0|}507|603|}
# flow 604: 508 -> 509 (Join -> Output_File)
{2010213001|XXGoport_dst_flow|308|0|408|0|{0|}508|604|}
{2010214001|XXGiport_src_flow|309|0|409|0|{0|}509|604|}

# ================= Prototype hints =================
{2010501005|XXGpvertex|30|0|700|0|{|prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|}}
{2010501005|XXGpvertex|32|0|701|0|{|prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|}}
{2010501005|XXGpvertex|35|0|702|0|{|prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|}}
{2010501005|XXGpvertex|31|0|703|0|{|prototype_path|$AB_COMPONENTS/Sort/Sort.mpc|}}
{2010501005|XXGpvertex|33|0|704|0|{|prototype_path|$AB_COMPONENTS/Sort/Sort.mpc|}}
{2010501005|XXGpvertex|34|0|705|0|{|prototype_path|$AB_COMPONENTS/Transform/Join.mpc|}}

# ================= PORTS + FLOWS INSIDE Graph4 (internals have real flows) =================
# Reformat(60) out -> Redefine_Format(61) in
{2010212001|XXGvertex_oport|260|0|360|0|{0|out|}60|560|}
{2010211001|XXGvertex_iport|261|0|361|0|{0|in|}61|561|}
{2010213001|XXGoport_dst_flow|360|0|460|0|{0|}560|660|}
{2010214001|XXGiport_src_flow|361|0|461|0|{0|}561|660|}
# Redefine_Format(61) out -> Filter_by_Expression(62) in
{2010212001|XXGvertex_oport|262|0|362|0|{0|out|}61|562|}
{2010211001|XXGvertex_iport|263|0|363|0|{0|in|}62|563|}
{2010213001|XXGoport_dst_flow|362|0|462|0|{0|}562|661|}
{2010214001|XXGiport_src_flow|363|0|463|0|{0|}563|661|}
# Filter_by_Expression(62) out -> Dedup_Sorted(63) in
{2010212001|XXGvertex_oport|264|0|364|0|{0|out|}62|564|}
{2010211001|XXGvertex_iport|265|0|365|0|{0|in|}63|565|}
{2010213001|XXGoport_dst_flow|364|0|464|0|{0|}564|662|}
{2010214001|XXGiport_src_flow|365|0|465|0|{0|}565|662|}
# Filter_by_Expression(62) reject -> Trash_1(64) in
{2010212001|XXGvertex_oport|266|0|366|0|{1|reject|}62|566|}
{2010211001|XXGvertex_iport|267|0|367|0|{0|in|}64|567|}
{2010213001|XXGoport_dst_flow|366|0|466|0|{0|}566|663|}
{2010214001|XXGiport_src_flow|367|0|467|0|{0|}567|663|}
# Redefine_Format_1(65) stands alone fed from Dedup (63) out
{2010212001|XXGvertex_oport|268|0|368|0|{0|out|}63|568|}
{2010211001|XXGvertex_iport|269|0|369|0|{0|in|}65|569|}
{2010213001|XXGoport_dst_flow|368|0|468|0|{0|}568|664|}
{2010214001|XXGiport_src_flow|369|0|469|0|{0|}569|664|}

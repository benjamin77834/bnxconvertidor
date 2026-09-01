@
{18|Type|XXGrepository|Primary_Name|XXGgraph|_ab_object_schema|0|_ab_semantic_schema|9|eme_flatten_format|1|schema_version|34|root_id|0|ent_count|90|rel_count|158|}
{2010001002|XXGdirectory|0|1|1|0|{@{}@}}
{2010600005|XXGgraph|1|0|1|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|_ab_semantic_schema|9|1|1|Hnl|@{0|}}
{30001002|XXparameter|_ab_has_render_fixups|2|1|1|Hl||{0|}}
{30001002|XXparameter|!ab_compatibility|4.1.3.4|3|9|P|@{0|}}
{30001002|XXparameter|_UseNewErrorLogDML|True|13|1|Hl||{0|}}
}}@0|@0|0|0|0|0|0|0|ADS_sample_gaph|dp90557|@1|100|-1|@9|@34817|{0|}0|0|{0|}{0|}{0|}{0|}1.0|798000|433000|7|}}
{2010703001|XXGgraphinfo|2|0|3|0|{@{}@1|4.0.3.3|{1|1|}Job 'ADS_sample_gaph' Execution Status Report

Job completed successfully at Tuesday, December 27, 2022 12:30:21
Run performed by user dp90557
||||@@33207807|}}
{2010705002|XXGrunsettings|3|0|5|0|{@{}@EDW DEV-1||||1|60|0|1|1|0|0|0|0|1|1|0|0|1|2|1|1|0|0|0|@16|}}
{2010242002|XXGface|4|0|7|0|{@{}@Arial|0|100|0|}}
{2010210004|XXGflow|5|0|9|0|{@{}@0|.5|.5|{0|}172|17|}}
{2010210004|XXGflow|6|0|11|0|{@{}@0|.5|.5|{0|}173|1041|}}
{2010210004|XXGflow|7|0|13|0|{@{}@0|.5|.5|{0|}174|17|}}
{2010210004|XXGflow|8|0|15|0|{@{}@0|.5|.5|{0|}162|17|}}
{2010210004|XXGflow|9|0|17|0|{@{}@0|.5|.5|{0|}165|1041|}}
{2010210004|XXGflow|10|0|19|0|{@{}@0|.5|.5|{0|}166|1041|}}
{2010210004|XXGflow|11|0|21|0|{@{}@0|.5|.5|{0|}168|17|}}
{2010600005|XXGgraph|12|0|23|0|{Subgraph created from graph "ADS_sample_gaph"|{}@0|@14000|11500|0|0|0|0|171|ADS Table Input|dp90557|@1|100|-1|@9|@32833|{0|}0|0|{0|}{0|}{0|}{0|}1.0|502000|168000|7|}}
{2010210004|XXGflow|13|0|25|0|{@{}@0|.5|.5|{0|}227|17|}}
{2010210004|XXGflow|14|0|27|0|{@{}@0|.5|.5|{0|}230|17|}}
{2010503005|XXGfvertex|15|0|29|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("read", "pdl") map_dataset 1 mapping [record dataset_path _interp_("/abinitio/ecscards/sit/data/serial/MX_CARDS_DWH/main/DRI_484_ADS_D.tmp", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|/abinitio/ecscards/sit/data/serial/MX_CARDS_DWH/main/DRI_484_ADS_D.tmp|3|2|$|@{0|}}
{30001002|XXparameter|read_metadata|// banamex/sr610891/111618/ADS_D.dml
// Schema File DML Generated: 2018-12-11 15:45:05 Version: 13269
type rec_t =
record
  string(1) V_REC_TYPE = NULL(' ');
  date("YYYY-MM-DD") D_PROCESS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(11) V_CASE_NBR = NULL('           ');
  string(23) V_ACQ_REF_NBR = NULL('                       ');
  string(19) V_CARD_NBR = NULL('                   ');
  string(3) V_ORG = NULL('   ');
  string(3) V_LOGO = NULL('   ');
  date("YYYY-MM-DD") D_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_STATUS = NULL(' ');
  date("YYYY-MM-DD") D_TRANS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_TRANS_CD = NULL('    ');
  decimal(12) N_ORIG_TRANS_AMT = NULL('            ');
  decimal(2) N_ORIG_TRANS_AMT_EXP = NULL('  ');
  decimal(4) N_ORIG_CURR_CD = NULL('    ');
  string(16) V_MERCH_ID = NULL('                ');
  string(4) V_MCC = NULL('    ');
  string(8) V_UPDATE_USERID = NULL('        ');
  date("YYYY-MM-DD") D_CREATE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(12) N_DISP_AMT = NULL('            ');
  decimal(2) N_DISP_AMT_EXP = NULL('  ');
  decimal(4) N_DISP_CURR_CD = NULL('    ');
  decimal(4) N_REASON_CD = NULL('    ');
  string(25) V_MERCH_NAME = NULL('                         ');
  string(3) V_MERCH_CNTRY = NULL('   ');
  string(5) V_IWI_INSTALL_NBR = NULL('     ');
  string(8) V_AUTH_CODE = NULL('        ');
  string(2) V_POS_MODE = NULL('  ');
  decimal(3) N_ECMMRCE_IND = NULL('   ');
  string(3) V_CASE_STATUS = NULL('   ');
  string(8) V_ASSIGNED_TO = NULL('        ');
  string(3) V_DISP_TYPE = NULL('   ');
  decimal(4) N_CLS_RSN_CD = NULL('    ');
  decimal(4) N_INIT_RSN_CD = NULL('    ');
  string(30) V_REMARKS = NULL('                              ');
  decimal(12) N_TRAN_TYPE = NULL('            ');
  string(10) V_SETTLEMENT_DATE = NULL('          ');
  string(20) V_MMT = NULL('                    ');
  decimal(1) N_DOC_IND = NULL(' ');
  decimal(6) N_PLAN = NULL('      ');
  string(3) V_MOD_ID = NULL('   ');
  string(6) V_LV = NULL('      ');
  string(1) V_TCR_E = NULL(' ');
  string(15) V_CLAIM_NBR = NULL('               ');
  string(3) V_PRIOR_CASE_STATUS = NULL('   ');
  string(1) V_SHIELD_IDENTIFICATION = NULL(' ');
  string(2) V_ACCT_STATUS = NULL('  ');
  string(12) V_UPDATE_TIME = NULL('            ');
  string(8) V_CREATE_USER_ID = NULL('        ');
  string(25) V_GROUP_DESC = NULL('                         ');
  string(8) V_GROUP_ID = NULL('        ');
  string(1) V_CARD_BLOCK_CODE = NULL(' ');
  string(2) V_CARD_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_CARD_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_CARD_BLOCK_TIME = NULL('        ');
  string(4) V_ACCT_BLOCK_CODE = NULL('    ');
  string(2) V_ACCT_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_ACCT_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_ACCT_BLOCK_TIME = NULL('        ');
  string(4) V_CHANNEL = NULL('    ');
  date("YYYY-MM-DD") D_AUTH_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_AUTH_TIME = NULL('        ');
  string(2) V_RESPONSE_CODE = NULL('  ');
  string(4) V_POS_ENTRY_MODE = NULL('    ');
  string(3) V_SERVICE_CODE = NULL('   ');
  string(3) V_ECI_MOTO_IND = NULL('   ');
  string(2) V_TERMINAL_CAPABILITY = NULL('  ');
  string(40) V_CREATE_USER = NULL('                                        ');
  string(30) V_CASE_STATUS_DESC = NULL('                              ');
  string(40) V_ANALYST_NAME = NULL('                                        ');
  string(1) V_SLA_IND = NULL(' ');
  string(25) V_ROLE_NAME = NULL('                         ');
  string(40) V_RSN_DESC = NULL('                                        ');
  string(80) V_DISP_TYPE_DESC = NULL('                                                                                ');
  string(40) V_BENEFIT_DESC = NULL('                                        ');
  string(10) V_PRODUCT_TYPE = NULL('          ');
  string(40) V_PRODUCT_DESC = NULL('                                        ');
  string(19) V_CUST_NBR = NULL('                   ');
  string(170) V_CUST_NAME = NULL('                                                                                                                                                                          ');
  string(15) V_CONTACT_NUM = NULL('               ');
  string(19) V_ACCT_NBR = NULL('                   ');
  string(10) V_PULL_SESSION_NBR = NULL('          ');
  string(40) V_DEPT_DESC = NULL('                                        ');
  string(10) V_BENEFIT_APP_DATE = NULL('          ');
  string(300) V_BDADSDWO_INI_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(300) V_BDADSDWO_CLS_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(15) V_BDADSDWO_MERCHANT_CITY = NULL('               ');
  string(15) V_BDADSDWO_CASE_FAV_AGAINST = NULL('               ');
  string(1) V_BDADSDWO_RECATIVE_IND = NULL(' ');
  string(15) V_BDADSDWO_PREV_CASE_NBR = NULL('               ');
  string(50) V_BDADSDWO_CONDUSEF_CNBR = NULL('                                                  ');
  string(4) V_BDADSDWO_ADSCTLG_RULE_NO = NULL('    ');
  string(40) V_BDADSDWO_ADSCTLG_RULE_DESC = NULL('                                        ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_SIRH = NULL('               ');
  string(15) V_BDADSDWO_CUS_SEG_ID = NULL('               ');
  string(19) V_DPAN_ACCT_NBR = NULL('                   ');
  string(1) V_WALLET_TXN_TOKEN_IND_CDE = NULL(' ');
  string(17) V_MT_WRITEOFF = NULL('                 ');
  string(4) V_ACCT_BRANCH_OPEN = NULL('    ');
  decimal(12) N_CONTRACT_NO = NULL('            ');
  date("YYYY-MM-DD") D_CANCEL_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_ACCT_STA_FLG = NULL(' ');
  string(4) V_ACCT_RESTR = NULL('    ');
  string(4) V_SUB_PROD_TY_CD = NULL('    ');
  string(1) V_SOURCE_TXN = NULL(' ');
  string(40) V_TRANS_DESC = NULL('                                        ');
  decimal(12) N_CHECK_NBR = NULL('            ');
  string(4) V_TXN_BRANCH = NULL('    ');
  string(2) V_BRANCH_CASH = NULL('  ');
  string(4) V_WFLOW_BRANCH = NULL('    ');
  string(8) V_WFLOW_SIRH = NULL('        ');
  string(3) V_CLIAM_ORIG = NULL('   ');
  decimal(12) N_WRITEOFF_AMT = NULL('            ');
  decimal(4) N_ADJ_REJ_CDE = NULL('    ');
  string(1) V_PAY_TYPE_CDE = NULL(' ');
  date("YYYY-MM-DD") D_CUTOFF_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(19) V_ADJ_ACCT = NULL('                   ');
  string(40) V_BENIF_NAME = NULL('                                        ');
  string(19) V_NON_CUS_NBR = NULL('                   ');
  string(20) V_PYMT_CONT_NBR = NULL('                    ');
  date("YYYY-MM-DD") D_POC_ISSUE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  date("YYYY-MM-DD") D_POC_PAY_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_POC_BRANCH = NULL('    ');
  date("YYYY-MM-DD") D_COMM_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(2) V_COMM_MODE = NULL('  ');
  string(40) V_CUST_STREET_NO = NULL('                                        ');
  string(25) V_CUST_CITY = NULL('                         ');
  string(20) V_CUST_STATE = NULL('                    ');
  decimal(6) N_CUST_ZIP_CODE = NULL('      ');
  decimal(15) N_CUST_PHONE = NULL('               ');
  string(40) V_CUST_MAIL = NULL('                                        ');
  decimal(4) N_TXN_APP_ID = NULL('    ');
  date("YYYY-MM-DD") D_EST_RES_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(27) V_PROB_FACTOR = NULL('                           ');
  decimal(2) N_SCORE_ERRCD = NULL('  ');
  decimal(17) N_DISP_AMT_LC = NULL('                 ');
  string(3) V_VCR_DISPUTE_CATEGORY = NULL('   ');
  string(6) V_VCR_DISP_STATUS = NULL('      ');
  string(1) V_VCR_IO_IND = NULL(' ');
  string(10) V_VISA_CASE_NBR = NULL('          ');
  string(11) V_VISA_FINANCIAL_ID = NULL('           ');
  string(9) V_QUICK_FORM_ID = NULL('         ');
  string(10) V_QUICK_FORM_TYPE = NULL('          ');
  string(100) V_VCR_CASE_STATUS = NULL('                                                                                                    ');
  string(15) V_FRD_CASE_NBR = NULL('               ');
  string(15) V_PRCL_CASE_NBR = NULL('               ');
  string(20) V_NETWORK_ID = NULL('                    ');
  string(20) V_INTL_ID_ATTR = NULL('                    ');
  string(20) V_INTL_ID_TRN_ATTR = NULL('                    ');
  string(10) V_FOLLOW_UP_DT = NULL('          ');
  decimal(4) N_DAYS_TO_ACT = NULL('    ');
  string(10) V_DATE_TO_RSP = NULL('          ');
  string(10) V_LAST_ACTION_DT = NULL('          ');
  string(20) V_BID_NAME = NULL('                    ');
  string(30) V_JURISDICTION = NULL('                              ');
  string(10) V_DC_CODE = NULL('          ');
  string(40) V_VCR_ACTION = NULL('                                        ');
  string(3) V_DISP_JURSDC_ATTR = NULL('   ');
  decimal(9) N_DISP_PREARB_ID = NULL('         ');
  string(8) V_PREARB_DISP_CAT = NULL('        ');
  string(6) V_DISPUTE_CONDITION = NULL('      ');
  string(1) V_FRAUD_TYPE = NULL(' ');
  date("YYYY-MM-DD") MIS_DATE =NULL('');
  string(1) V_BNPL_IND  = NULL(' ');
  string(2) V_CHIP_PIN_IND = NULL('  '); /*filler field*/
  string(19) V_CLAIM_ID = NULL('                   ');
  string(8) V_CLAIM_TYPE = NULL('        ');
  string(12) V_RETRIEVAL_ID = NULL('            ');
  string(12) V_CHARGEBACK_ID = NULL('            ');
  string(30) V_CHARGEBACK_TYPE = NULL('                              ');
  string(12) V_FRAUD_ID = NULL('            ');
  string(12) V_FEE_ID = NULL('            ');
  string(3) V_AUTH_INDICATORS_CHP = NULL('   ');
  string(3) V_AUTH_INDICATORS_ATM = NULL('   ');
  string(3) V_AUTH_INDICATORS_3DS = NULL('   ');
  string(3) V_AUTH_INDICATORS_CV2 = NULL('   ');
  string(3) V_AUTH_INDICATORS_2FA = NULL('   ');
  string(3) V_AUTH_INDICATORS_WLL = NULL('   ');
  decimal(11) N_MDES_TOKEN_REQID = NULL('           ');
  string(2) N_MDES_TOKEN_B026 = NULL('  ');
  string(1) V_MDES_TOKEN_B027 = NULL(' ');
  decimal(2) N_MDES_TOKEN_ASURLVL = NULL('  ');
  string(2) V_MDES_TKNSTR_TYP = NULL('  ');
  string(2) N_MDES_PREVAL_IND = NULL('  ');
  string(1) V_MDES_PREVAL_RSLT = NULL(' ');
  decimal(3) V_MDES_DSRP_TRAN_ID = NULL('   ');
  string(3) V_CUST_CELL_PHN_SRC = NULL('   ');
  string(3) V_CUST_MAIL_SRC = NULL('   ');
  string(1) V_3DS2_PGM_PROTO = NULL(' ');
  string(1) V_3DS2_EC_3DS_IND = NULL(' ');
  string(36) V_3DS2_DS_TXN_ID = NULL('                                    ');
  string(1) V_3DS2_IAV_PRS_IND = NULL(' ');
  string(1) V_3DS2_IAV_VL_RLT = NULL(' ');
  string(15) V_NCE_IP_INIT = NULL('               ');
  string(17) V_NCE_MAC_ORIGIN = NULL('                 ');
  string(40) V_CUS_SEG_NAME = NULL('                                        ');
  decimal(4) N_ORIG_DBT_TRNS_CD = NULL('    ');
  date("YYYY-MM-DD") V_REACTV_DATE = NULL('');
  string(4) V_REJ_CODE = NULL('    ');
  string(48) V_REJ_DESC = NULL('                                                ');
  string(1) V_WLL_CRYPTOGRAM = NULL(' ');
  string(16) V_ARQC_CRYPTOGRAM = NULL('                ');
  string(2) V_ARQC_VALID_IND = NULL('  ');
  string(20) V_MERCHANT_STATE_NAME = NULL('                    ');
  string(23) V_NUM_REFADQUIRENTE = NULL('                       ');
  date('YYYY-MM-DD') D_FECHA_COMPRA = NULL("");
  decimal(13,2) N_IMP_TRNMONDESTINO =NULL('             ');
  string(50) V_TYPE_REFOUND = NULL('                                                  ');
  decimal(4) N_HIERARCHY =  NULL('    ');
  string("\\n") V_FILLER = NULL('');
  end;
metadata type = 
record
  string(1) V_REC_TYPE = NULL(' ');
  date("YYYY-MM-DD") D_PROCESS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(11) V_CASE_NBR = NULL('           ');
  string(23) V_ACQ_REF_NBR = NULL('                       ');
  string(19) V_CARD_NBR = NULL('                   ');
  string(3) V_ORG = NULL('   ');
  string(3) V_LOGO = NULL('   ');
  date("YYYY-MM-DD") D_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_STATUS = NULL(' ');
  date("YYYY-MM-DD") D_TRANS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_TRANS_CD = NULL('    ');
  decimal(12) N_ORIG_TRANS_AMT = NULL('            ');
  decimal(2) N_ORIG_TRANS_AMT_EXP = NULL('  ');
  decimal(4) N_ORIG_CURR_CD = NULL('    ');
  string(16) V_MERCH_ID = NULL('                ');
  string(4) V_MCC = NULL('    ');
  string(8) V_UPDATE_USERID = NULL('        ');
  date("YYYY-MM-DD") D_CREATE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(12) N_DISP_AMT = NULL('            ');
  decimal(2) N_DISP_AMT_EXP = NULL('  ');
  decimal(4) N_DISP_CURR_CD = NULL('    ');
  decimal(4) N_REASON_CD = NULL('    ');
  string(25) V_MERCH_NAME = NULL('                         ');
  string(3) V_MERCH_CNTRY = NULL('   ');
  string(5) V_IWI_INSTALL_NBR = NULL('     ');
  string(8) V_AUTH_CODE = NULL('        ');
  string(2) V_POS_MODE = NULL('  ');
  decimal(3) N_ECMMRCE_IND = NULL('   ');
  string(3) V_CASE_STATUS = NULL('   ');
  string(8) V_ASSIGNED_TO = NULL('        ');
  string(3) V_DISP_TYPE = NULL('   ');
  decimal(4) N_CLS_RSN_CD = NULL('    ');
  decimal(4) N_INIT_RSN_CD = NULL('    ');
  string(30) V_REMARKS = NULL('                              ');
  decimal(12) N_TRAN_TYPE = NULL('            ');
  string(10) V_SETTLEMENT_DATE = NULL('          ');
  string(20) V_MMT = NULL('                    ');
  decimal(1) N_DOC_IND = NULL(' ');
  decimal(6) N_PLAN = NULL('      ');
  string(3) V_MOD_ID = NULL('   ');
  string(6) V_LV = NULL('      ');
  string(1) V_TCR_E = NULL(' ');
  string(15) V_CLAIM_NBR = NULL('               ');
  string(3) V_PRIOR_CASE_STATUS = NULL('   ');
  string(1) V_SHIELD_IDENTIFICATION = NULL(' ');
  string(2) V_ACCT_STATUS = NULL('  ');
  string(12) V_UPDATE_TIME = NULL('            ');
  string(8) V_CREATE_USER_ID = NULL('        ');
  string(25) V_GROUP_DESC = NULL('                         ');
  string(8) V_GROUP_ID = NULL('        ');
  string(1) V_CARD_BLOCK_CODE = NULL(' ');
  string(2) V_CARD_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_CARD_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_CARD_BLOCK_TIME = NULL('        ');
  string(4) V_ACCT_BLOCK_CODE = NULL('    ');
  string(2) V_ACCT_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_ACCT_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_ACCT_BLOCK_TIME = NULL('        ');
  string(4) V_CHANNEL = NULL('    ');
  date("YYYY-MM-DD") D_AUTH_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_AUTH_TIME = NULL('        ');
  string(2) V_RESPONSE_CODE = NULL('  ');
  string(4) V_POS_ENTRY_MODE = NULL('    ');
  string(3) V_SERVICE_CODE = NULL('   ');
  string(3) V_ECI_MOTO_IND = NULL('   ');
  string(2) V_TERMINAL_CAPABILITY = NULL('  ');
  string(40) V_CREATE_USER = NULL('                                        ');
  string(30) V_CASE_STATUS_DESC = NULL('                              ');
  string(40) V_ANALYST_NAME = NULL('                                        ');
  string(1) V_SLA_IND = NULL(' ');
  string(25) V_ROLE_NAME = NULL('                         ');
  string(40) V_RSN_DESC = NULL('                                        ');
  string(80) V_DISP_TYPE_DESC = NULL('                                                                                ');
  string(40) V_BENEFIT_DESC = NULL('                                        ');
  string(10) V_PRODUCT_TYPE = NULL('          ');
  string(40) V_PRODUCT_DESC = NULL('                                        ');
  string(19) V_CUST_NBR = NULL('                   ');
  string(170) V_CUST_NAME = NULL('                                                                                                                                                                          ');
  string(15) V_CONTACT_NUM = NULL('               ');
  string(19) V_ACCT_NBR = NULL('                   ');
  string(10) V_PULL_SESSION_NBR = NULL('          ');
  string(40) V_DEPT_DESC = NULL('                                        ');
  string(10) V_BENEFIT_APP_DATE = NULL('          ');
  string(300) V_BDADSDWO_INI_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(300) V_BDADSDWO_CLS_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(15) V_BDADSDWO_MERCHANT_CITY = NULL('               ');
  string(15) V_BDADSDWO_CASE_FAV_AGAINST = NULL('               ');
  string(1) V_BDADSDWO_RECATIVE_IND = NULL(' ');
  string(15) V_BDADSDWO_PREV_CASE_NBR = NULL('               ');
  string(50) V_BDADSDWO_CONDUSEF_CNBR = NULL('                                                  ');
  string(4) V_BDADSDWO_ADSCTLG_RULE_NO = NULL('    ');
  string(40) V_BDADSDWO_ADSCTLG_RULE_DESC = NULL('                                        ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_SIRH = NULL('               ');
  string(15) V_BDADSDWO_CUS_SEG_ID = NULL('               ');
  string(19) V_DPAN_ACCT_NBR = NULL('                   ');
  string(1) V_WALLET_TXN_TOKEN_IND_CDE = NULL(' ');
  string(17) V_MT_WRITEOFF = NULL('                 ');
  string(4) V_ACCT_BRANCH_OPEN = NULL('    ');
  decimal(12) N_CONTRACT_NO = NULL('            ');
  date("YYYY-MM-DD") D_CANCEL_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_ACCT_STA_FLG = NULL(' ');
  string(4) V_ACCT_RESTR = NULL('    ');
  string(4) V_SUB_PROD_TY_CD = NULL('    ');
  string(1) V_SOURCE_TXN = NULL(' ');
  string(40) V_TRANS_DESC = NULL('                                        ');
  decimal(12) N_CHECK_NBR = NULL('            ');
  string(4) V_TXN_BRANCH = NULL('    ');
  string(2) V_BRANCH_CASH = NULL('  ');
  string(4) V_WFLOW_BRANCH = NULL('    ');
  string(8) V_WFLOW_SIRH = NULL('        ');
  string(3) V_CLIAM_ORIG = NULL('   ');
  decimal(12) N_WRITEOFF_AMT = NULL('            ');
  decimal(4) N_ADJ_REJ_CDE = NULL('    ');
  string(1) V_PAY_TYPE_CDE = NULL(' ');
  date("YYYY-MM-DD") D_CUTOFF_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(19) V_ADJ_ACCT = NULL('                   ');
  string(40) V_BENIF_NAME = NULL('                                        ');
  string(19) V_NON_CUS_NBR = NULL('                   ');
  string(20) V_PYMT_CONT_NBR = NULL('                    ');
  date("YYYY-MM-DD") D_POC_ISSUE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  date("YYYY-MM-DD") D_POC_PAY_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_POC_BRANCH = NULL('    ');
  date("YYYY-MM-DD") D_COMM_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(2) V_COMM_MODE = NULL('  ');
  string(40) V_CUST_STREET_NO = NULL('                                        ');
  string(25) V_CUST_CITY = NULL('                         ');
  string(20) V_CUST_STATE = NULL('                    ');
  decimal(6) N_CUST_ZIP_CODE = NULL('      ');
  decimal(15) N_CUST_PHONE = NULL('               ');
  string(40) V_CUST_MAIL = NULL('                                        ');
  decimal(4) N_TXN_APP_ID = NULL('    ');
  date("YYYY-MM-DD") D_EST_RES_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(27) V_PROB_FACTOR = NULL('                           ');
  decimal(2) N_SCORE_ERRCD = NULL('  ');
  decimal(17) N_DISP_AMT_LC = NULL('                 ');
  string(3) V_VCR_DISPUTE_CATEGORY = NULL('   ');
  string(6) V_VCR_DISP_STATUS = NULL('      ');
  string(1) V_VCR_IO_IND = NULL(' ');
  string(10) V_VISA_CASE_NBR = NULL('          ');
  string(11) V_VISA_FINANCIAL_ID = NULL('           ');
  string(9) V_QUICK_FORM_ID = NULL('         ');
  string(10) V_QUICK_FORM_TYPE = NULL('          ');
  string(100) V_VCR_CASE_STATUS = NULL('                                                                                                    ');
  string(15) V_FRD_CASE_NBR = NULL('               ');
  string(15) V_PRCL_CASE_NBR = NULL('               ');
  string(20) V_NETWORK_ID = NULL('                    ');
  string(20) V_INTL_ID_ATTR = NULL('                    ');
  string(20) V_INTL_ID_TRN_ATTR = NULL('                    ');
  string(10) V_FOLLOW_UP_DT = NULL('          ');
  decimal(4) N_DAYS_TO_ACT = NULL('    ');
  string(10) V_DATE_TO_RSP = NULL('          ');
  string(10) V_LAST_ACTION_DT = NULL('          ');
  string(20) V_BID_NAME = NULL('                    ');
  string(30) V_JURISDICTION = NULL('                              ');
  string(10) V_DC_CODE = NULL('          ');
  string(40) V_VCR_ACTION = NULL('                                        ');
  string(3) V_DISP_JURSDC_ATTR = NULL('   ');
  decimal(9) N_DISP_PREARB_ID = NULL('         ');
  string(8) V_PREARB_DISP_CAT = NULL('        ');
  string(6) V_DISPUTE_CONDITION = NULL('      ');
  string(1) V_FRAUD_TYPE = NULL(' ');
  date("YYYY-MM-DD") MIS_DATE =NULL('');
  string(1) V_BNPL_IND  = NULL(' ');
  string(19) V_CLAIM_ID = NULL('                   ');
  string(8) V_CLAIM_TYPE = NULL('        ');
  string(12) V_RETRIEVAL_ID = NULL('            ');
  string(12) V_CHARGEBACK_ID = NULL('            ');
  string(30) V_CHARGEBACK_TYPE = NULL('                              ');
  string(12) V_FRAUD_ID = NULL('            ');
  string(12) V_FEE_ID = NULL('            ');
  string(3) V_AUTH_INDICATORS_CHP = NULL('   ');
  string(3) V_AUTH_INDICATORS_ATM = NULL('   ');
  string(3) V_AUTH_INDICATORS_3DS = NULL('   ');
  string(3) V_AUTH_INDICATORS_CV2 = NULL('   ');
  string(3) V_AUTH_INDICATORS_2FA = NULL('   ');
  string(3) V_AUTH_INDICATORS_WLL = NULL('   ');
  decimal(11) N_MDES_TOKEN_REQID = NULL('           ');
  string(2) N_MDES_TOKEN_B026 = NULL('  ');
  string(1) V_MDES_TOKEN_B027 = NULL(' ');
  decimal(2) N_MDES_TOKEN_ASURLVL = NULL('  ');
  string(2) V_MDES_TKNSTR_TYP = NULL('  ');
  string(2) N_MDES_PREVAL_IND = NULL('  ');
  string(1) V_MDES_PREVAL_RSLT = NULL(' ');
  decimal(3) V_MDES_DSRP_TRAN_ID = NULL('   ');
  string(3) V_CUST_CELL_PHN_SRC = NULL('   ');
  string(3) V_CUST_MAIL_SRC = NULL('   ');
  string(1) V_3DS2_PGM_PROTO = NULL(' ');
  string(1) V_3DS2_EC_3DS_IND = NULL(' ');
  string(36) V_3DS2_DS_TXN_ID = NULL('                                    ');
  string(1) V_3DS2_IAV_PRS_IND = NULL(' ');
  string(1) V_3DS2_IAV_VL_RLT = NULL(' ');
  string(50) V_NCE_IP_INIT = NULL('                                                  ');
  string(20) V_NCE_MAC_ORIGIN = NULL('                    ');
  string(40) V_CUS_SEG_NAME = NULL('                                        ');
  decimal(4) N_ORIG_DBT_TRNS_CD = NULL('    ');
  date("YYYY-MM-DD") V_REACTV_DATE = NULL('');
  string(4) V_REJ_CODE = NULL('    ');
  string(48) V_REJ_DESC = NULL('                                                ');
  string(1) V_WLL_CRYPTOGRAM = NULL(' ');
  string(16) V_ARQC_CRYPTOGRAM = NULL('                ');
  string(2) V_ARQC_VALID_IND = NULL('  ');
  string(20) V_MERCHANT_STATE_NAME = NULL('                    ');
  string(23) V_NUM_REFADQUIRENTE = NULL('                       ');
  date('YYYY-MM-DD') D_FECHA_COMPRA = NULL("");
  decimal(13,2) N_IMP_TRNMONDESTINO =NULL('             ');
  string(50) V_TYPE_REFOUND = NULL('                                                  ');
  decimal(4) N_HIERARCHY =  NULL('    ');
  string("\\n") V_FILLER = NULL('');
  end;|3|1|l|@{0|}}
}}@0|Input File|45000|85000|0|0|0|0|200|Input File-3|Ab Initio Software|@1|1000|-1||6||33089|-1|-1|}}
{2010203004|XXGoport|16|0|31|0|{@{}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|17|0|34|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0001|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|create_directories|False|13|1|FKl|If True, create any parent directories as necessary|{0|}}
{30001002|XXparameter|create_directories.display_name|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.keyword|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.condition|version 4.1.1.r9.0:|3|15|P?|@{0|}}
{30001002|XXparameter|translate_format|False|13|1|Fl|If true, translate the file format.|{0|}}
{30001002|XXparameter|translate_format.condition|version 4.0.0.r1.0:|3|15|P?|@{0|}}
{30001002|XXparameter|format|uninterpreted|15|1|FKl|'uninterpreted' (raw data), 'seqfile' (Hadoop sequence file), 'parquet' (Parquet format), 'orc' (ORC format), 'avro' (Avro format), 'texttable' (Hive text table).|{6|uninterpreted|seqfile|parquet|orc|avro|texttable|}}
{30001002|XXparameter|format.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoopy_condition|value format uninterpreted False value format * True default constant False|13|13|Hv|Hidden condition for deciding hadoop-codec visibility|{0|}}
{30001002|XXparameter|hadoopy_condition.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoop_codec|Uncompressed|15|1|FKl|Compression for writing hadoop specific file format. orc=\{ZLIB,SNAPPY,LZO\}, parquet=\{GZIP,SNAPPY,LZO\}, seqfile=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZO\}, avro=\{SNAPPY,Deflate,BZIP2\}, texttable=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4\}|{8|Uncompressed|GZIP|SNAPPY|Deflate|BZIP2|ZLIB|LZ4|LZO|}}
{30001002|XXparameter|hadoop_codec.display_name|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.keyword|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.condition|param_exact hadoopy_condition True param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed only_last_key_instance orc_file|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url||28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|either_or|value block_compressed True True sameas keep_on_disk default constant True|13|13|v|Either B-C or K-o-D|{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if the block compressed lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|mode lookup version 2.15.5.r34: param_exact either_or True|3|15|P?|@{0|}}
{30001002|XXparameter|only_last_key_instance|False|13|1|Fl|Match only the last instance of each key|{0|}}
{30001002|XXparameter|only_last_key_instance.condition|mode lookup version 3.0.2.r12.0:|3|15|P?|@{0|}}
{30001002|XXparameter|orc_file|False|13|1|Fl|Set to true if it is Hive ORC file|{0|}}
{30001002|XXparameter|orc_file.condition|mode lookup version 3.2.2.r15.0: param_exact direct_addressed True param_exact block_compressed False|3|15|P?|@{0|}}
{30001002|XXparameter|Layout||28|2|RF$||{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
{30001002|XXparameter|mpcmodtime|1649796511|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|read_metadata||7|1|RFsl||{0|}}
}}@0|Input File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010203004|XXGoport|18|0|36|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|19|0|39|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("/abinitio/ecscards/sit/data/serial/MX_CARDS_DWH/main/DRI_484_ADS_D.tmp_1", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|write_metadata|// banamex/sr610891/111618/ADS_D.dml
// Schema File DML Generated: 2018-12-11 15:45:05 Version: 13269
type rec_t =
record
  string(1) V_REC_TYPE = NULL(' ');
  date("YYYY-MM-DD") D_PROCESS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(11) V_CASE_NBR = NULL('           ');
  string(23) V_ACQ_REF_NBR = NULL('                       ');
  string(19) V_CARD_NBR = NULL('                   ');
  string(3) V_ORG = NULL('   ');
  string(3) V_LOGO = NULL('   ');
  date("YYYY-MM-DD") D_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_STATUS = NULL(' ');
  date("YYYY-MM-DD") D_TRANS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_TRANS_CD = NULL('    ');
  decimal(12) N_ORIG_TRANS_AMT = NULL('            ');
  decimal(2) N_ORIG_TRANS_AMT_EXP = NULL('  ');
  decimal(4) N_ORIG_CURR_CD = NULL('    ');
  string(16) V_MERCH_ID = NULL('                ');
  string(4) V_MCC = NULL('    ');
  string(8) V_UPDATE_USERID = NULL('        ');
  date("YYYY-MM-DD") D_CREATE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(12) N_DISP_AMT = NULL('            ');
  decimal(2) N_DISP_AMT_EXP = NULL('  ');
  decimal(4) N_DISP_CURR_CD = NULL('    ');
  decimal(4) N_REASON_CD = NULL('    ');
  string(25) V_MERCH_NAME = NULL('                         ');
  string(3) V_MERCH_CNTRY = NULL('   ');
  string(5) V_IWI_INSTALL_NBR = NULL('     ');
  string(8) V_AUTH_CODE = NULL('        ');
  string(2) V_POS_MODE = NULL('  ');
  decimal(3) N_ECMMRCE_IND = NULL('   ');
  string(3) V_CASE_STATUS = NULL('   ');
  string(8) V_ASSIGNED_TO = NULL('        ');
  string(3) V_DISP_TYPE = NULL('   ');
  decimal(4) N_CLS_RSN_CD = NULL('    ');
  decimal(4) N_INIT_RSN_CD = NULL('    ');
  string(30) V_REMARKS = NULL('                              ');
  decimal(12) N_TRAN_TYPE = NULL('            ');
  string(10) V_SETTLEMENT_DATE = NULL('          ');
  string(20) V_MMT = NULL('                    ');
  decimal(1) N_DOC_IND = NULL(' ');
  decimal(6) N_PLAN = NULL('      ');
  string(3) V_MOD_ID = NULL('   ');
  string(6) V_LV = NULL('      ');
  string(1) V_TCR_E = NULL(' ');
  string(15) V_CLAIM_NBR = NULL('               ');
  string(3) V_PRIOR_CASE_STATUS = NULL('   ');
  string(1) V_SHIELD_IDENTIFICATION = NULL(' ');
  string(2) V_ACCT_STATUS = NULL('  ');
  string(12) V_UPDATE_TIME = NULL('            ');
  string(8) V_CREATE_USER_ID = NULL('        ');
  string(25) V_GROUP_DESC = NULL('                         ');
  string(8) V_GROUP_ID = NULL('        ');
  string(1) V_CARD_BLOCK_CODE = NULL(' ');
  string(2) V_CARD_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_CARD_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_CARD_BLOCK_TIME = NULL('        ');
  string(4) V_ACCT_BLOCK_CODE = NULL('    ');
  string(2) V_ACCT_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_ACCT_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_ACCT_BLOCK_TIME = NULL('        ');
  string(4) V_CHANNEL = NULL('    ');
  date("YYYY-MM-DD") D_AUTH_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_AUTH_TIME = NULL('        ');
  string(2) V_RESPONSE_CODE = NULL('  ');
  string(4) V_POS_ENTRY_MODE = NULL('    ');
  string(3) V_SERVICE_CODE = NULL('   ');
  string(3) V_ECI_MOTO_IND = NULL('   ');
  string(2) V_TERMINAL_CAPABILITY = NULL('  ');
  string(40) V_CREATE_USER = NULL('                                        ');
  string(30) V_CASE_STATUS_DESC = NULL('                              ');
  string(40) V_ANALYST_NAME = NULL('                                        ');
  string(1) V_SLA_IND = NULL(' ');
  string(25) V_ROLE_NAME = NULL('                         ');
  string(40) V_RSN_DESC = NULL('                                        ');
  string(80) V_DISP_TYPE_DESC = NULL('                                                                                ');
  string(40) V_BENEFIT_DESC = NULL('                                        ');
  string(10) V_PRODUCT_TYPE = NULL('          ');
  string(40) V_PRODUCT_DESC = NULL('                                        ');
  string(19) V_CUST_NBR = NULL('                   ');
  string(170) V_CUST_NAME = NULL('                                                                                                                                                                          ');
  string(15) V_CONTACT_NUM = NULL('               ');
  string(19) V_ACCT_NBR = NULL('                   ');
  string(10) V_PULL_SESSION_NBR = NULL('          ');
  string(40) V_DEPT_DESC = NULL('                                        ');
  string(10) V_BENEFIT_APP_DATE = NULL('          ');
  string(300) V_BDADSDWO_INI_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(300) V_BDADSDWO_CLS_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(15) V_BDADSDWO_MERCHANT_CITY = NULL('               ');
  string(15) V_BDADSDWO_CASE_FAV_AGAINST = NULL('               ');
  string(1) V_BDADSDWO_RECATIVE_IND = NULL(' ');
  string(15) V_BDADSDWO_PREV_CASE_NBR = NULL('               ');
  string(50) V_BDADSDWO_CONDUSEF_CNBR = NULL('                                                  ');
  string(4) V_BDADSDWO_ADSCTLG_RULE_NO = NULL('    ');
  string(40) V_BDADSDWO_ADSCTLG_RULE_DESC = NULL('                                        ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_SIRH = NULL('               ');
  string(15) V_BDADSDWO_CUS_SEG_ID = NULL('               ');
  string(19) V_DPAN_ACCT_NBR = NULL('                   ');
  string(1) V_WALLET_TXN_TOKEN_IND_CDE = NULL(' ');
  string(17) V_MT_WRITEOFF = NULL('                 ');
  string(4) V_ACCT_BRANCH_OPEN = NULL('    ');
  decimal(12) N_CONTRACT_NO = NULL('            ');
  date("YYYY-MM-DD") D_CANCEL_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_ACCT_STA_FLG = NULL(' ');
  string(4) V_ACCT_RESTR = NULL('    ');
  string(4) V_SUB_PROD_TY_CD = NULL('    ');
  string(1) V_SOURCE_TXN = NULL(' ');
  string(40) V_TRANS_DESC = NULL('                                        ');
  decimal(12) N_CHECK_NBR = NULL('            ');
  string(4) V_TXN_BRANCH = NULL('    ');
  string(2) V_BRANCH_CASH = NULL('  ');
  string(4) V_WFLOW_BRANCH = NULL('    ');
  string(8) V_WFLOW_SIRH = NULL('        ');
  string(3) V_CLIAM_ORIG = NULL('   ');
  decimal(12) N_WRITEOFF_AMT = NULL('            ');
  decimal(4) N_ADJ_REJ_CDE = NULL('    ');
  string(1) V_PAY_TYPE_CDE = NULL(' ');
  date("YYYY-MM-DD") D_CUTOFF_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(19) V_ADJ_ACCT = NULL('                   ');
  string(40) V_BENIF_NAME = NULL('                                        ');
  string(19) V_NON_CUS_NBR = NULL('                   ');
  string(20) V_PYMT_CONT_NBR = NULL('                    ');
  date("YYYY-MM-DD") D_POC_ISSUE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  date("YYYY-MM-DD") D_POC_PAY_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_POC_BRANCH = NULL('    ');
  date("YYYY-MM-DD") D_COMM_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(2) V_COMM_MODE = NULL('  ');
  string(40) V_CUST_STREET_NO = NULL('                                        ');
  string(25) V_CUST_CITY = NULL('                         ');
  string(20) V_CUST_STATE = NULL('                    ');
  decimal(6) N_CUST_ZIP_CODE = NULL('      ');
  decimal(15) N_CUST_PHONE = NULL('               ');
  string(40) V_CUST_MAIL = NULL('                                        ');
  decimal(4) N_TXN_APP_ID = NULL('    ');
  date("YYYY-MM-DD") D_EST_RES_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(27) V_PROB_FACTOR = NULL('                           ');
  decimal(2) N_SCORE_ERRCD = NULL('  ');
  decimal(17) N_DISP_AMT_LC = NULL('                 ');
  string(3) V_VCR_DISPUTE_CATEGORY = NULL('   ');
  string(6) V_VCR_DISP_STATUS = NULL('      ');
  string(1) V_VCR_IO_IND = NULL(' ');
  string(10) V_VISA_CASE_NBR = NULL('          ');
  string(11) V_VISA_FINANCIAL_ID = NULL('           ');
  string(9) V_QUICK_FORM_ID = NULL('         ');
  string(10) V_QUICK_FORM_TYPE = NULL('          ');
  string(100) V_VCR_CASE_STATUS = NULL('                                                                                                    ');
  string(15) V_FRD_CASE_NBR = NULL('               ');
  string(15) V_PRCL_CASE_NBR = NULL('               ');
  string(20) V_NETWORK_ID = NULL('                    ');
  string(20) V_INTL_ID_ATTR = NULL('                    ');
  string(20) V_INTL_ID_TRN_ATTR = NULL('                    ');
  string(10) V_FOLLOW_UP_DT = NULL('          ');
  decimal(4) N_DAYS_TO_ACT = NULL('    ');
  string(10) V_DATE_TO_RSP = NULL('          ');
  string(10) V_LAST_ACTION_DT = NULL('          ');
  string(20) V_BID_NAME = NULL('                    ');
  string(30) V_JURISDICTION = NULL('                              ');
  string(10) V_DC_CODE = NULL('          ');
  string(40) V_VCR_ACTION = NULL('                                        ');
  string(3) V_DISP_JURSDC_ATTR = NULL('   ');
  decimal(9) N_DISP_PREARB_ID = NULL('         ');
  string(8) V_PREARB_DISP_CAT = NULL('        ');
  string(6) V_DISPUTE_CONDITION = NULL('      ');
  string(1) V_FRAUD_TYPE = NULL(' ');
  date("YYYY-MM-DD") MIS_DATE =NULL('');
  string(1) V_BNPL_IND  = NULL(' ');
  string(2) V_CHIP_PIN_IND = NULL('  '); /*filler field*/
  string(19) V_CLAIM_ID = NULL('                   ');
  string(8) V_CLAIM_TYPE = NULL('        ');
  string(12) V_RETRIEVAL_ID = NULL('            ');
  string(12) V_CHARGEBACK_ID = NULL('            ');
  string(30) V_CHARGEBACK_TYPE = NULL('                              ');
  string(12) V_FRAUD_ID = NULL('            ');
  string(12) V_FEE_ID = NULL('            ');
  string(3) V_AUTH_INDICATORS_CHP = NULL('   ');
  string(3) V_AUTH_INDICATORS_ATM = NULL('   ');
  string(3) V_AUTH_INDICATORS_3DS = NULL('   ');
  string(3) V_AUTH_INDICATORS_CV2 = NULL('   ');
  string(3) V_AUTH_INDICATORS_2FA = NULL('   ');
  string(3) V_AUTH_INDICATORS_WLL = NULL('   ');
  decimal(11) N_MDES_TOKEN_REQID = NULL('           ');
  string(2) N_MDES_TOKEN_B026 = NULL('  ');
  string(1) V_MDES_TOKEN_B027 = NULL(' ');
  decimal(2) N_MDES_TOKEN_ASURLVL = NULL('  ');
  string(2) V_MDES_TKNSTR_TYP = NULL('  ');
  string(2) N_MDES_PREVAL_IND = NULL('  ');
  string(1) V_MDES_PREVAL_RSLT = NULL(' ');
  decimal(3) V_MDES_DSRP_TRAN_ID = NULL('   ');
  string(3) V_CUST_CELL_PHN_SRC = NULL('   ');
  string(3) V_CUST_MAIL_SRC = NULL('   ');
  string(1) V_3DS2_PGM_PROTO = NULL(' ');
  string(1) V_3DS2_EC_3DS_IND = NULL(' ');
  string(36) V_3DS2_DS_TXN_ID = NULL('                                    ');
  string(1) V_3DS2_IAV_PRS_IND = NULL(' ');
  string(1) V_3DS2_IAV_VL_RLT = NULL(' ');
  string(15) V_NCE_IP_INIT = NULL('               ');
  string(17) V_NCE_MAC_ORIGIN = NULL('                 ');
  string(40) V_CUS_SEG_NAME = NULL('                                        ');
  decimal(4) N_ORIG_DBT_TRNS_CD = NULL('    ');
  date("YYYY-MM-DD") V_REACTV_DATE = NULL('');
  string(4) V_REJ_CODE = NULL('    ');
  string(48) V_REJ_DESC = NULL('                                                ');
  string(1) V_WLL_CRYPTOGRAM = NULL(' ');
  string(16) V_ARQC_CRYPTOGRAM = NULL('                ');
  string(2) V_ARQC_VALID_IND = NULL('  ');
  string(20) V_MERCHANT_STATE_NAME = NULL('                    ');
  string(23) V_NUM_REFADQUIRENTE = NULL('                       ');
  date('YYYY-MM-DD') D_FECHA_COMPRA = NULL("");
  decimal(13,2) N_IMP_TRNMONDESTINO =NULL('             ');
  string(50) V_TYPE_REFOUND = NULL('                                                  ');
  decimal(4) N_HIERARCHY =  NULL('    ');
  string("\\n") V_FILLER = NULL('');
  end;
metadata type = 
record
  string(1) V_REC_TYPE = NULL(' ');
  date("YYYY-MM-DD") D_PROCESS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(11) V_CASE_NBR = NULL('           ');
  string(23) V_ACQ_REF_NBR = NULL('                       ');
  string(19) V_CARD_NBR = NULL('                   ');
  string(3) V_ORG = NULL('   ');
  string(3) V_LOGO = NULL('   ');
  date("YYYY-MM-DD") D_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_STATUS = NULL(' ');
  date("YYYY-MM-DD") D_TRANS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_TRANS_CD = NULL('    ');
  decimal(12) N_ORIG_TRANS_AMT = NULL('            ');
  decimal(2) N_ORIG_TRANS_AMT_EXP = NULL('  ');
  decimal(4) N_ORIG_CURR_CD = NULL('    ');
  string(16) V_MERCH_ID = NULL('                ');
  string(4) V_MCC = NULL('    ');
  string(8) V_UPDATE_USERID = NULL('        ');
  date("YYYY-MM-DD") D_CREATE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(12) N_DISP_AMT = NULL('            ');
  decimal(2) N_DISP_AMT_EXP = NULL('  ');
  decimal(4) N_DISP_CURR_CD = NULL('    ');
  decimal(4) N_REASON_CD = NULL('    ');
  string(25) V_MERCH_NAME = NULL('                         ');
  string(3) V_MERCH_CNTRY = NULL('   ');
  string(5) V_IWI_INSTALL_NBR = NULL('     ');
  string(8) V_AUTH_CODE = NULL('        ');
  string(2) V_POS_MODE = NULL('  ');
  decimal(3) N_ECMMRCE_IND = NULL('   ');
  string(3) V_CASE_STATUS = NULL('   ');
  string(8) V_ASSIGNED_TO = NULL('        ');
  string(3) V_DISP_TYPE = NULL('   ');
  decimal(4) N_CLS_RSN_CD = NULL('    ');
  decimal(4) N_INIT_RSN_CD = NULL('    ');
  string(30) V_REMARKS = NULL('                              ');
  decimal(12) N_TRAN_TYPE = NULL('            ');
  string(10) V_SETTLEMENT_DATE = NULL('          ');
  string(20) V_MMT = NULL('                    ');
  decimal(1) N_DOC_IND = NULL(' ');
  decimal(6) N_PLAN = NULL('      ');
  string(3) V_MOD_ID = NULL('   ');
  string(6) V_LV = NULL('      ');
  string(1) V_TCR_E = NULL(' ');
  string(15) V_CLAIM_NBR = NULL('               ');
  string(3) V_PRIOR_CASE_STATUS = NULL('   ');
  string(1) V_SHIELD_IDENTIFICATION = NULL(' ');
  string(2) V_ACCT_STATUS = NULL('  ');
  string(12) V_UPDATE_TIME = NULL('            ');
  string(8) V_CREATE_USER_ID = NULL('        ');
  string(25) V_GROUP_DESC = NULL('                         ');
  string(8) V_GROUP_ID = NULL('        ');
  string(1) V_CARD_BLOCK_CODE = NULL(' ');
  string(2) V_CARD_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_CARD_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_CARD_BLOCK_TIME = NULL('        ');
  string(4) V_ACCT_BLOCK_CODE = NULL('    ');
  string(2) V_ACCT_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_ACCT_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_ACCT_BLOCK_TIME = NULL('        ');
  string(4) V_CHANNEL = NULL('    ');
  date("YYYY-MM-DD") D_AUTH_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_AUTH_TIME = NULL('        ');
  string(2) V_RESPONSE_CODE = NULL('  ');
  string(4) V_POS_ENTRY_MODE = NULL('    ');
  string(3) V_SERVICE_CODE = NULL('   ');
  string(3) V_ECI_MOTO_IND = NULL('   ');
  string(2) V_TERMINAL_CAPABILITY = NULL('  ');
  string(40) V_CREATE_USER = NULL('                                        ');
  string(30) V_CASE_STATUS_DESC = NULL('                              ');
  string(40) V_ANALYST_NAME = NULL('                                        ');
  string(1) V_SLA_IND = NULL(' ');
  string(25) V_ROLE_NAME = NULL('                         ');
  string(40) V_RSN_DESC = NULL('                                        ');
  string(80) V_DISP_TYPE_DESC = NULL('                                                                                ');
  string(40) V_BENEFIT_DESC = NULL('                                        ');
  string(10) V_PRODUCT_TYPE = NULL('          ');
  string(40) V_PRODUCT_DESC = NULL('                                        ');
  string(19) V_CUST_NBR = NULL('                   ');
  string(170) V_CUST_NAME = NULL('                                                                                                                                                                          ');
  string(15) V_CONTACT_NUM = NULL('               ');
  string(19) V_ACCT_NBR = NULL('                   ');
  string(10) V_PULL_SESSION_NBR = NULL('          ');
  string(40) V_DEPT_DESC = NULL('                                        ');
  string(10) V_BENEFIT_APP_DATE = NULL('          ');
  string(300) V_BDADSDWO_INI_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(300) V_BDADSDWO_CLS_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(15) V_BDADSDWO_MERCHANT_CITY = NULL('               ');
  string(15) V_BDADSDWO_CASE_FAV_AGAINST = NULL('               ');
  string(1) V_BDADSDWO_RECATIVE_IND = NULL(' ');
  string(15) V_BDADSDWO_PREV_CASE_NBR = NULL('               ');
  string(50) V_BDADSDWO_CONDUSEF_CNBR = NULL('                                                  ');
  string(4) V_BDADSDWO_ADSCTLG_RULE_NO = NULL('    ');
  string(40) V_BDADSDWO_ADSCTLG_RULE_DESC = NULL('                                        ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_SIRH = NULL('               ');
  string(15) V_BDADSDWO_CUS_SEG_ID = NULL('               ');
  string(19) V_DPAN_ACCT_NBR = NULL('                   ');
  string(1) V_WALLET_TXN_TOKEN_IND_CDE = NULL(' ');
  string(17) V_MT_WRITEOFF = NULL('                 ');
  string(4) V_ACCT_BRANCH_OPEN = NULL('    ');
  decimal(12) N_CONTRACT_NO = NULL('            ');
  date("YYYY-MM-DD") D_CANCEL_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_ACCT_STA_FLG = NULL(' ');
  string(4) V_ACCT_RESTR = NULL('    ');
  string(4) V_SUB_PROD_TY_CD = NULL('    ');
  string(1) V_SOURCE_TXN = NULL(' ');
  string(40) V_TRANS_DESC = NULL('                                        ');
  decimal(12) N_CHECK_NBR = NULL('            ');
  string(4) V_TXN_BRANCH = NULL('    ');
  string(2) V_BRANCH_CASH = NULL('  ');
  string(4) V_WFLOW_BRANCH = NULL('    ');
  string(8) V_WFLOW_SIRH = NULL('        ');
  string(3) V_CLIAM_ORIG = NULL('   ');
  decimal(12) N_WRITEOFF_AMT = NULL('            ');
  decimal(4) N_ADJ_REJ_CDE = NULL('    ');
  string(1) V_PAY_TYPE_CDE = NULL(' ');
  date("YYYY-MM-DD") D_CUTOFF_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(19) V_ADJ_ACCT = NULL('                   ');
  string(40) V_BENIF_NAME = NULL('                                        ');
  string(19) V_NON_CUS_NBR = NULL('                   ');
  string(20) V_PYMT_CONT_NBR = NULL('                    ');
  date("YYYY-MM-DD") D_POC_ISSUE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  date("YYYY-MM-DD") D_POC_PAY_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_POC_BRANCH = NULL('    ');
  date("YYYY-MM-DD") D_COMM_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(2) V_COMM_MODE = NULL('  ');
  string(40) V_CUST_STREET_NO = NULL('                                        ');
  string(25) V_CUST_CITY = NULL('                         ');
  string(20) V_CUST_STATE = NULL('                    ');
  decimal(6) N_CUST_ZIP_CODE = NULL('      ');
  decimal(15) N_CUST_PHONE = NULL('               ');
  string(40) V_CUST_MAIL = NULL('                                        ');
  decimal(4) N_TXN_APP_ID = NULL('    ');
  date("YYYY-MM-DD") D_EST_RES_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(27) V_PROB_FACTOR = NULL('                           ');
  decimal(2) N_SCORE_ERRCD = NULL('  ');
  decimal(17) N_DISP_AMT_LC = NULL('                 ');
  string(3) V_VCR_DISPUTE_CATEGORY = NULL('   ');
  string(6) V_VCR_DISP_STATUS = NULL('      ');
  string(1) V_VCR_IO_IND = NULL(' ');
  string(10) V_VISA_CASE_NBR = NULL('          ');
  string(11) V_VISA_FINANCIAL_ID = NULL('           ');
  string(9) V_QUICK_FORM_ID = NULL('         ');
  string(10) V_QUICK_FORM_TYPE = NULL('          ');
  string(100) V_VCR_CASE_STATUS = NULL('                                                                                                    ');
  string(15) V_FRD_CASE_NBR = NULL('               ');
  string(15) V_PRCL_CASE_NBR = NULL('               ');
  string(20) V_NETWORK_ID = NULL('                    ');
  string(20) V_INTL_ID_ATTR = NULL('                    ');
  string(20) V_INTL_ID_TRN_ATTR = NULL('                    ');
  string(10) V_FOLLOW_UP_DT = NULL('          ');
  decimal(4) N_DAYS_TO_ACT = NULL('    ');
  string(10) V_DATE_TO_RSP = NULL('          ');
  string(10) V_LAST_ACTION_DT = NULL('          ');
  string(20) V_BID_NAME = NULL('                    ');
  string(30) V_JURISDICTION = NULL('                              ');
  string(10) V_DC_CODE = NULL('          ');
  string(40) V_VCR_ACTION = NULL('                                        ');
  string(3) V_DISP_JURSDC_ATTR = NULL('   ');
  decimal(9) N_DISP_PREARB_ID = NULL('         ');
  string(8) V_PREARB_DISP_CAT = NULL('        ');
  string(6) V_DISPUTE_CONDITION = NULL('      ');
  string(1) V_FRAUD_TYPE = NULL(' ');
  date("YYYY-MM-DD") MIS_DATE =NULL('');
  string(1) V_BNPL_IND  = NULL(' ');
  string(19) V_CLAIM_ID = NULL('                   ');
  string(8) V_CLAIM_TYPE = NULL('        ');
  string(12) V_RETRIEVAL_ID = NULL('            ');
  string(12) V_CHARGEBACK_ID = NULL('            ');
  string(30) V_CHARGEBACK_TYPE = NULL('                              ');
  string(12) V_FRAUD_ID = NULL('            ');
  string(12) V_FEE_ID = NULL('            ');
  string(3) V_AUTH_INDICATORS_CHP = NULL('   ');
  string(3) V_AUTH_INDICATORS_ATM = NULL('   ');
  string(3) V_AUTH_INDICATORS_3DS = NULL('   ');
  string(3) V_AUTH_INDICATORS_CV2 = NULL('   ');
  string(3) V_AUTH_INDICATORS_2FA = NULL('   ');
  string(3) V_AUTH_INDICATORS_WLL = NULL('   ');
  decimal(11) N_MDES_TOKEN_REQID = NULL('           ');
  string(2) N_MDES_TOKEN_B026 = NULL('  ');
  string(1) V_MDES_TOKEN_B027 = NULL(' ');
  decimal(2) N_MDES_TOKEN_ASURLVL = NULL('  ');
  string(2) V_MDES_TKNSTR_TYP = NULL('  ');
  string(2) N_MDES_PREVAL_IND = NULL('  ');
  string(1) V_MDES_PREVAL_RSLT = NULL(' ');
  decimal(3) V_MDES_DSRP_TRAN_ID = NULL('   ');
  string(3) V_CUST_CELL_PHN_SRC = NULL('   ');
  string(3) V_CUST_MAIL_SRC = NULL('   ');
  string(1) V_3DS2_PGM_PROTO = NULL(' ');
  string(1) V_3DS2_EC_3DS_IND = NULL(' ');
  string(36) V_3DS2_DS_TXN_ID = NULL('                                    ');
  string(1) V_3DS2_IAV_PRS_IND = NULL(' ');
  string(1) V_3DS2_IAV_VL_RLT = NULL(' ');
  string(50) V_NCE_IP_INIT = NULL('                                                  ');
  string(20) V_NCE_MAC_ORIGIN = NULL('                    ');
  string(40) V_CUS_SEG_NAME = NULL('                                        ');
  decimal(4) N_ORIG_DBT_TRNS_CD = NULL('    ');
  date("YYYY-MM-DD") V_REACTV_DATE = NULL('');
  string(4) V_REJ_CODE = NULL('    ');
  string(48) V_REJ_DESC = NULL('                                                ');
  string(1) V_WLL_CRYPTOGRAM = NULL(' ');
  string(16) V_ARQC_CRYPTOGRAM = NULL('                ');
  string(2) V_ARQC_VALID_IND = NULL('  ');
  string(20) V_MERCHANT_STATE_NAME = NULL('                    ');
  string(23) V_NUM_REFADQUIRENTE = NULL('                       ');
  date('YYYY-MM-DD') D_FECHA_COMPRA = NULL("");
  decimal(13,2) N_IMP_TRNMONDESTINO =NULL('             ');
  string(50) V_TYPE_REFOUND = NULL('                                                  ');
  decimal(4) N_HIERARCHY =  NULL('    ');
  string("\\n") V_FILLER = NULL('');
  end;|3|1|l|@{0|}}
{30001002|XXparameter|mode|0x0062|3|2|$|@{0|}}
{30001002|XXparameter|Layout|/abinitio/ecscards/sit/data/serial/MX_CARDS_DWH/main/DRI_484_ADS_D.tmp_1|3|2|$|@{0|}}
}}@0|Input File|395000|85000|0|0|0|0|231|Input File-4|Ab Initio Software|@1|1000|-1||6||33089|-1|-1|}}
{2010202004|XXGiport|20|0|41|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|21|0|44|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0001|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|create_directories|False|13|1|FKl|If True, create any parent directories as necessary|{0|}}
{30001002|XXparameter|create_directories.display_name|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.keyword|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.condition|version 4.1.1.r9.0:|3|15|P?|@{0|}}
{30001002|XXparameter|translate_format|False|13|1|Fl|If true, translate the file format.|{0|}}
{30001002|XXparameter|translate_format.condition|version 4.0.0.r1.0:|3|15|P?|@{0|}}
{30001002|XXparameter|format|uninterpreted|15|1|FKl|'uninterpreted' (raw data), 'seqfile' (Hadoop sequence file), 'parquet' (Parquet format), 'orc' (ORC format), 'avro' (Avro format), 'texttable' (Hive text table).|{6|uninterpreted|seqfile|parquet|orc|avro|texttable|}}
{30001002|XXparameter|format.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoopy_condition|value format uninterpreted False value format * True default constant False|13|13|Hv|Hidden condition for deciding hadoop-codec visibility|{0|}}
{30001002|XXparameter|hadoopy_condition.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoop_codec|Uncompressed|15|1|FKl|Compression for writing hadoop specific file format. orc=\{ZLIB,SNAPPY,LZO\}, parquet=\{GZIP,SNAPPY,LZO\}, seqfile=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZO\}, avro=\{SNAPPY,Deflate,BZIP2\}, texttable=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4\}|{8|Uncompressed|GZIP|SNAPPY|Deflate|BZIP2|ZLIB|LZ4|LZO|}}
{30001002|XXparameter|hadoop_codec.display_name|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.keyword|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.condition|param_exact hadoopy_condition True param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed only_last_key_instance orc_file|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url||28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|either_or|value block_compressed True True sameas keep_on_disk default constant True|13|13|v|Either B-C or K-o-D|{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if the block compressed lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|mode lookup version 2.15.5.r34: param_exact either_or True|3|15|P?|@{0|}}
{30001002|XXparameter|only_last_key_instance|False|13|1|Fl|Match only the last instance of each key|{0|}}
{30001002|XXparameter|only_last_key_instance.condition|mode lookup version 3.0.2.r12.0:|3|15|P?|@{0|}}
{30001002|XXparameter|orc_file|False|13|1|Fl|Set to true if it is Hive ORC file|{0|}}
{30001002|XXparameter|orc_file.condition|mode lookup version 3.2.2.r15.0: param_exact direct_addressed True param_exact block_compressed False|3|15|P?|@{0|}}
{30001002|XXparameter|Layout||28|2|RF$||{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
{30001002|XXparameter|mpcmodtime|1649796511|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|write_metadata||7|1|RFsl||{0|}}
}}@0|Input File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010202004|XXGiport|22|0|46|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010501005|XXGpvertex|23|0|49|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
{30001002|XXparameter|out0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|transform0|out :: reformat(in) =
begin
  out.* :: in.*;
  out.V_NUM_REFADQUIRENTE :: 'ABC';
  out.D_FECHA_COMPRA :: '0001-01-01';
  out.N_IMP_TRNMONDESTINO :: 123;
  out.V_TYPE_REFOUND :: 'ABC';
  out.N_HIERARCHY :: 123;
end;|3|1|l|@{0|}}
}}@0|Reformat|177000|63000|0|0|0|0|229|Reformat-1|Ab Initio Software|Built-in 1.0:|1|100|0||6||32833|1|{1|0|}}}
{2010203004|XXGoport|24|0|51|0|{@{}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|25|0|54|0|{@{}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|26|0|56|0|{@{}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|27|0|58|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|28|0|60|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|29|0|63|0|{Changes the record format of your data by dropping fields or by using DML expressions to add fields, combine fields, or modify the data.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|reformat-transform|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|count|1|1|1|Fl|Number of reformat transforms|{0|}}
{30001002|XXparameter|count.is_index|true|3|9|P|@{0|}}
{30001002|XXparameter|transform0||8|1|FOl|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
{30001002|XXparameter|select||20|2|FK$|Filter expression before reformatting|{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version :2.12.999.m999|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword2|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword2.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp ramp_keyword2 ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|output_index||8|1|FKl|Output index computation|{0|}}
{30001002|XXparameter|output_index.display_name|output-index|3|9|P|@{0|}}
{30001002|XXparameter|output_index.keyword|output-index|3|9|P|@{0|}}
{30001002|XXparameter|output_index_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_index_port.display_name|output-index_port|3|9|P|@{0|}}
{30001002|XXparameter|output_index_port.keyword|output-index_port|3|9|P|@{0|}}
{30001002|XXparameter|output_index_signature|int output_index_out::output_index(in)|3|2|H$|Function returning index of output port|{0|}}
{30001002|XXparameter|output_index_signature.display_name|output-index_signature|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes||8|1|FKl|Output index vector computation|{0|}}
{30001002|XXparameter|output_indexes.display_name|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes.keyword|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_indexes_port.display_name|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port.keyword|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_signature|int[int] output_indexes_out::output_indexes(in)|3|2|H$|Function returning vector of indexes of output ports|{0|}}
{30001002|XXparameter|output_indexes_signature.display_name|output-indexes_signature|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|num_operations|7|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|out::reformat(in)|3|2|H$|Reformat operation|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out*|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|legacy_xfr;reject*=in;out*=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select)|3|2|H$||{0|}}
{30001002|XXparameter|num_types|3|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type3|event_info_t event_info "record int event_type; end"|3|2|H$|Information about the kind of event that happened|{0|}}
{30001002|XXparameter|operation2|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation3|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation6|optional out::output_at_event(event_info)|3|2|H$|Function to allow the output of an additional record at event|{0|}}
{30001002|XXparameter|operation7|optional ::on_startup(long in_recovery)|3|2|H$|Function executed at graph startup|{0|}}
{30001002|XXparameter|num_callbacks|6|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|main_mp_port|count out|3|1|l||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject0_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error0_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out[*],reject[*],error[*],log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1649796515|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Reformat|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|30|0|65|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform0||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|31|0|69|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|32|0|72|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|33|0|75|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|34|0|78|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|35|0|85|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Concatenate.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Concatenate|596000|258000|0|0|0|0|167|Concatenate|Ab Initio Software|Built-in 1.0:|1|100|0||6||1|1|{1|0|}}}
{2010203004|XXGoport|36|0|87|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|37|0|90|0|{@{}@0|0|0|0|in|0.0|@@@18195|0|}}
{2010501005|XXGpvertex|38|0|95|0|{Appends multiple flow partitions of data records one after another.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|concat|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|deadlock_prone|True|13|1|l|Necessary record on one input stops read on all inputs|{0|}}
{30001002|XXparameter|deadlock_prone.display_name|deadlock-prone|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=exact(in)|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis|fan_in_ok|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1649796515|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|Concatenate|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|39|0|97|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|40|0|100|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@18195|0|}}
{2010503005|XXGfvertex|41|0|103|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("/fct/ecscards/SECS000u13.BBD.DNLOAD.DWH.ADS.EP.20270927_New", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|write_metadata|// banamex/sr610891/111618/ADS_D.dml
// Schema File DML Generated: 2018-12-11 15:45:05 Version: 13269
type rec_t =
record
  string(1) V_REC_TYPE = NULL(' ');
  date("YYYY-MM-DD") D_PROCESS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(11) V_CASE_NBR = NULL('           ');
  string(23) V_ACQ_REF_NBR = NULL('                       ');
  string(19) V_CARD_NBR = NULL('                   ');
  string(3) V_ORG = NULL('   ');
  string(3) V_LOGO = NULL('   ');
  date("YYYY-MM-DD") D_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_STATUS = NULL(' ');
  date("YYYY-MM-DD") D_TRANS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_TRANS_CD = NULL('    ');
  decimal(12) N_ORIG_TRANS_AMT = NULL('            ');
  decimal(2) N_ORIG_TRANS_AMT_EXP = NULL('  ');
  decimal(4) N_ORIG_CURR_CD = NULL('    ');
  string(16) V_MERCH_ID = NULL('                ');
  string(4) V_MCC = NULL('    ');
  string(8) V_UPDATE_USERID = NULL('        ');
  date("YYYY-MM-DD") D_CREATE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(12) N_DISP_AMT = NULL('            ');
  decimal(2) N_DISP_AMT_EXP = NULL('  ');
  decimal(4) N_DISP_CURR_CD = NULL('    ');
  decimal(4) N_REASON_CD = NULL('    ');
  string(25) V_MERCH_NAME = NULL('                         ');
  string(3) V_MERCH_CNTRY = NULL('   ');
  string(5) V_IWI_INSTALL_NBR = NULL('     ');
  string(8) V_AUTH_CODE = NULL('        ');
  string(2) V_POS_MODE = NULL('  ');
  decimal(3) N_ECMMRCE_IND = NULL('   ');
  string(3) V_CASE_STATUS = NULL('   ');
  string(8) V_ASSIGNED_TO = NULL('        ');
  string(3) V_DISP_TYPE = NULL('   ');
  decimal(4) N_CLS_RSN_CD = NULL('    ');
  decimal(4) N_INIT_RSN_CD = NULL('    ');
  string(30) V_REMARKS = NULL('                              ');
  decimal(12) N_TRAN_TYPE = NULL('            ');
  string(10) V_SETTLEMENT_DATE = NULL('          ');
  string(20) V_MMT = NULL('                    ');
  decimal(1) N_DOC_IND = NULL(' ');
  decimal(6) N_PLAN = NULL('      ');
  string(3) V_MOD_ID = NULL('   ');
  string(6) V_LV = NULL('      ');
  string(1) V_TCR_E = NULL(' ');
  string(15) V_CLAIM_NBR = NULL('               ');
  string(3) V_PRIOR_CASE_STATUS = NULL('   ');
  string(1) V_SHIELD_IDENTIFICATION = NULL(' ');
  string(2) V_ACCT_STATUS = NULL('  ');
  string(12) V_UPDATE_TIME = NULL('            ');
  string(8) V_CREATE_USER_ID = NULL('        ');
  string(25) V_GROUP_DESC = NULL('                         ');
  string(8) V_GROUP_ID = NULL('        ');
  string(1) V_CARD_BLOCK_CODE = NULL(' ');
  string(2) V_CARD_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_CARD_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_CARD_BLOCK_TIME = NULL('        ');
  string(4) V_ACCT_BLOCK_CODE = NULL('    ');
  string(2) V_ACCT_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_ACCT_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_ACCT_BLOCK_TIME = NULL('        ');
  string(4) V_CHANNEL = NULL('    ');
  date("YYYY-MM-DD") D_AUTH_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_AUTH_TIME = NULL('        ');
  string(2) V_RESPONSE_CODE = NULL('  ');
  string(4) V_POS_ENTRY_MODE = NULL('    ');
  string(3) V_SERVICE_CODE = NULL('   ');
  string(3) V_ECI_MOTO_IND = NULL('   ');
  string(2) V_TERMINAL_CAPABILITY = NULL('  ');
  string(40) V_CREATE_USER = NULL('                                        ');
  string(30) V_CASE_STATUS_DESC = NULL('                              ');
  string(40) V_ANALYST_NAME = NULL('                                        ');
  string(1) V_SLA_IND = NULL(' ');
  string(25) V_ROLE_NAME = NULL('                         ');
  string(40) V_RSN_DESC = NULL('                                        ');
  string(80) V_DISP_TYPE_DESC = NULL('                                                                                ');
  string(40) V_BENEFIT_DESC = NULL('                                        ');
  string(10) V_PRODUCT_TYPE = NULL('          ');
  string(40) V_PRODUCT_DESC = NULL('                                        ');
  string(19) V_CUST_NBR = NULL('                   ');
  string(170) V_CUST_NAME = NULL('                                                                                                                                                                          ');
  string(15) V_CONTACT_NUM = NULL('               ');
  string(19) V_ACCT_NBR = NULL('                   ');
  string(10) V_PULL_SESSION_NBR = NULL('          ');
  string(40) V_DEPT_DESC = NULL('                                        ');
  string(10) V_BENEFIT_APP_DATE = NULL('          ');
  string(300) V_BDADSDWO_INI_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(300) V_BDADSDWO_CLS_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(15) V_BDADSDWO_MERCHANT_CITY = NULL('               ');
  string(15) V_BDADSDWO_CASE_FAV_AGAINST = NULL('               ');
  string(1) V_BDADSDWO_RECATIVE_IND = NULL(' ');
  string(15) V_BDADSDWO_PREV_CASE_NBR = NULL('               ');
  string(50) V_BDADSDWO_CONDUSEF_CNBR = NULL('                                                  ');
  string(4) V_BDADSDWO_ADSCTLG_RULE_NO = NULL('    ');
  string(40) V_BDADSDWO_ADSCTLG_RULE_DESC = NULL('                                        ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_SIRH = NULL('               ');
  string(15) V_BDADSDWO_CUS_SEG_ID = NULL('               ');
  string(19) V_DPAN_ACCT_NBR = NULL('                   ');
  string(1) V_WALLET_TXN_TOKEN_IND_CDE = NULL(' ');
  string(17) V_MT_WRITEOFF = NULL('                 ');
  string(4) V_ACCT_BRANCH_OPEN = NULL('    ');
  decimal(12) N_CONTRACT_NO = NULL('            ');
  date("YYYY-MM-DD") D_CANCEL_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_ACCT_STA_FLG = NULL(' ');
  string(4) V_ACCT_RESTR = NULL('    ');
  string(4) V_SUB_PROD_TY_CD = NULL('    ');
  string(1) V_SOURCE_TXN = NULL(' ');
  string(40) V_TRANS_DESC = NULL('                                        ');
  decimal(12) N_CHECK_NBR = NULL('            ');
  string(4) V_TXN_BRANCH = NULL('    ');
  string(2) V_BRANCH_CASH = NULL('  ');
  string(4) V_WFLOW_BRANCH = NULL('    ');
  string(8) V_WFLOW_SIRH = NULL('        ');
  string(3) V_CLIAM_ORIG = NULL('   ');
  decimal(12) N_WRITEOFF_AMT = NULL('            ');
  decimal(4) N_ADJ_REJ_CDE = NULL('    ');
  string(1) V_PAY_TYPE_CDE = NULL(' ');
  date("YYYY-MM-DD") D_CUTOFF_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(19) V_ADJ_ACCT = NULL('                   ');
  string(40) V_BENIF_NAME = NULL('                                        ');
  string(19) V_NON_CUS_NBR = NULL('                   ');
  string(20) V_PYMT_CONT_NBR = NULL('                    ');
  date("YYYY-MM-DD") D_POC_ISSUE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  date("YYYY-MM-DD") D_POC_PAY_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_POC_BRANCH = NULL('    ');
  date("YYYY-MM-DD") D_COMM_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(2) V_COMM_MODE = NULL('  ');
  string(40) V_CUST_STREET_NO = NULL('                                        ');
  string(25) V_CUST_CITY = NULL('                         ');
  string(20) V_CUST_STATE = NULL('                    ');
  decimal(6) N_CUST_ZIP_CODE = NULL('      ');
  decimal(15) N_CUST_PHONE = NULL('               ');
  string(40) V_CUST_MAIL = NULL('                                        ');
  decimal(4) N_TXN_APP_ID = NULL('    ');
  date("YYYY-MM-DD") D_EST_RES_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(27) V_PROB_FACTOR = NULL('                           ');
  decimal(2) N_SCORE_ERRCD = NULL('  ');
  decimal(17) N_DISP_AMT_LC = NULL('                 ');
  string(3) V_VCR_DISPUTE_CATEGORY = NULL('   ');
  string(6) V_VCR_DISP_STATUS = NULL('      ');
  string(1) V_VCR_IO_IND = NULL(' ');
  string(10) V_VISA_CASE_NBR = NULL('          ');
  string(11) V_VISA_FINANCIAL_ID = NULL('           ');
  string(9) V_QUICK_FORM_ID = NULL('         ');
  string(10) V_QUICK_FORM_TYPE = NULL('          ');
  string(100) V_VCR_CASE_STATUS = NULL('                                                                                                    ');
  string(15) V_FRD_CASE_NBR = NULL('               ');
  string(15) V_PRCL_CASE_NBR = NULL('               ');
  string(20) V_NETWORK_ID = NULL('                    ');
  string(20) V_INTL_ID_ATTR = NULL('                    ');
  string(20) V_INTL_ID_TRN_ATTR = NULL('                    ');
  string(10) V_FOLLOW_UP_DT = NULL('          ');
  decimal(4) N_DAYS_TO_ACT = NULL('    ');
  string(10) V_DATE_TO_RSP = NULL('          ');
  string(10) V_LAST_ACTION_DT = NULL('          ');
  string(20) V_BID_NAME = NULL('                    ');
  string(30) V_JURISDICTION = NULL('                              ');
  string(10) V_DC_CODE = NULL('          ');
  string(40) V_VCR_ACTION = NULL('                                        ');
  string(3) V_DISP_JURSDC_ATTR = NULL('   ');
  decimal(9) N_DISP_PREARB_ID = NULL('         ');
  string(8) V_PREARB_DISP_CAT = NULL('        ');
  string(6) V_DISPUTE_CONDITION = NULL('      ');
  string(1) V_FRAUD_TYPE = NULL(' ');
  date("YYYY-MM-DD") MIS_DATE =NULL('');
  string(1) V_BNPL_IND  = NULL(' ');
  string(2) V_CHIP_PIN_IND = NULL('  '); /*filler field*/
  string(19) V_CLAIM_ID = NULL('                   ');
  string(8) V_CLAIM_TYPE = NULL('        ');
  string(12) V_RETRIEVAL_ID = NULL('            ');
  string(12) V_CHARGEBACK_ID = NULL('            ');
  string(30) V_CHARGEBACK_TYPE = NULL('                              ');
  string(12) V_FRAUD_ID = NULL('            ');
  string(12) V_FEE_ID = NULL('            ');
  string(3) V_AUTH_INDICATORS_CHP = NULL('   ');
  string(3) V_AUTH_INDICATORS_ATM = NULL('   ');
  string(3) V_AUTH_INDICATORS_3DS = NULL('   ');
  string(3) V_AUTH_INDICATORS_CV2 = NULL('   ');
  string(3) V_AUTH_INDICATORS_2FA = NULL('   ');
  string(3) V_AUTH_INDICATORS_WLL = NULL('   ');
  decimal(11) N_MDES_TOKEN_REQID = NULL('           ');
  string(2) N_MDES_TOKEN_B026 = NULL('  ');
  string(1) V_MDES_TOKEN_B027 = NULL(' ');
  decimal(2) N_MDES_TOKEN_ASURLVL = NULL('  ');
  string(2) V_MDES_TKNSTR_TYP = NULL('  ');
  string(2) N_MDES_PREVAL_IND = NULL('  ');
  string(1) V_MDES_PREVAL_RSLT = NULL(' ');
  decimal(3) V_MDES_DSRP_TRAN_ID = NULL('   ');
  string(3) V_CUST_CELL_PHN_SRC = NULL('   ');
  string(3) V_CUST_MAIL_SRC = NULL('   ');
  string(1) V_3DS2_PGM_PROTO = NULL(' ');
  string(1) V_3DS2_EC_3DS_IND = NULL(' ');
  string(36) V_3DS2_DS_TXN_ID = NULL('                                    ');
  string(1) V_3DS2_IAV_PRS_IND = NULL(' ');
  string(1) V_3DS2_IAV_VL_RLT = NULL(' ');
  string(15) V_NCE_IP_INIT = NULL('               ');
  string(17) V_NCE_MAC_ORIGIN = NULL('                 ');
  string(40) V_CUS_SEG_NAME = NULL('                                        ');
  decimal(4) N_ORIG_DBT_TRNS_CD = NULL('    ');
  date("YYYY-MM-DD") V_REACTV_DATE = NULL('');
  string(4) V_REJ_CODE = NULL('    ');
  string(48) V_REJ_DESC = NULL('                                                ');
  string(1) V_WLL_CRYPTOGRAM = NULL(' ');
  string(16) V_ARQC_CRYPTOGRAM = NULL('                ');
  string(2) V_ARQC_VALID_IND = NULL('  ');
  string(20) V_MERCHANT_STATE_NAME = NULL('                    ');
  string(23) V_NUM_REFADQUIRENTE = NULL('                       ');
  date('YYYY-MM-DD') D_FECHA_COMPRA = NULL("");
  decimal(13,2) N_IMP_TRNMONDESTINO =NULL('             ');
  string(50) V_TYPE_REFOUND = NULL('                                                  ');
  decimal(4) N_HIERARCHY =  NULL('    ');
  string("\\n") V_FILLER = NULL('');
  end;
metadata type = 
record
  string(1) V_REC_TYPE = NULL(' ');
  date("YYYY-MM-DD") D_PROCESS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(11) V_CASE_NBR = NULL('           ');
  string(23) V_ACQ_REF_NBR = NULL('                       ');
  string(19) V_CARD_NBR = NULL('                   ');
  string(3) V_ORG = NULL('   ');
  string(3) V_LOGO = NULL('   ');
  date("YYYY-MM-DD") D_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_STATUS = NULL(' ');
  date("YYYY-MM-DD") D_TRANS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_TRANS_CD = NULL('    ');
  decimal(12) N_ORIG_TRANS_AMT = NULL('            ');
  decimal(2) N_ORIG_TRANS_AMT_EXP = NULL('  ');
  decimal(4) N_ORIG_CURR_CD = NULL('    ');
  string(16) V_MERCH_ID = NULL('                ');
  string(4) V_MCC = NULL('    ');
  string(8) V_UPDATE_USERID = NULL('        ');
  date("YYYY-MM-DD") D_CREATE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(12) N_DISP_AMT = NULL('            ');
  decimal(2) N_DISP_AMT_EXP = NULL('  ');
  decimal(4) N_DISP_CURR_CD = NULL('    ');
  decimal(4) N_REASON_CD = NULL('    ');
  string(25) V_MERCH_NAME = NULL('                         ');
  string(3) V_MERCH_CNTRY = NULL('   ');
  string(5) V_IWI_INSTALL_NBR = NULL('     ');
  string(8) V_AUTH_CODE = NULL('        ');
  string(2) V_POS_MODE = NULL('  ');
  decimal(3) N_ECMMRCE_IND = NULL('   ');
  string(3) V_CASE_STATUS = NULL('   ');
  string(8) V_ASSIGNED_TO = NULL('        ');
  string(3) V_DISP_TYPE = NULL('   ');
  decimal(4) N_CLS_RSN_CD = NULL('    ');
  decimal(4) N_INIT_RSN_CD = NULL('    ');
  string(30) V_REMARKS = NULL('                              ');
  decimal(12) N_TRAN_TYPE = NULL('            ');
  string(10) V_SETTLEMENT_DATE = NULL('          ');
  string(20) V_MMT = NULL('                    ');
  decimal(1) N_DOC_IND = NULL(' ');
  decimal(6) N_PLAN = NULL('      ');
  string(3) V_MOD_ID = NULL('   ');
  string(6) V_LV = NULL('      ');
  string(1) V_TCR_E = NULL(' ');
  string(15) V_CLAIM_NBR = NULL('               ');
  string(3) V_PRIOR_CASE_STATUS = NULL('   ');
  string(1) V_SHIELD_IDENTIFICATION = NULL(' ');
  string(2) V_ACCT_STATUS = NULL('  ');
  string(12) V_UPDATE_TIME = NULL('            ');
  string(8) V_CREATE_USER_ID = NULL('        ');
  string(25) V_GROUP_DESC = NULL('                         ');
  string(8) V_GROUP_ID = NULL('        ');
  string(1) V_CARD_BLOCK_CODE = NULL(' ');
  string(2) V_CARD_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_CARD_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_CARD_BLOCK_TIME = NULL('        ');
  string(4) V_ACCT_BLOCK_CODE = NULL('    ');
  string(2) V_ACCT_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_ACCT_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_ACCT_BLOCK_TIME = NULL('        ');
  string(4) V_CHANNEL = NULL('    ');
  date("YYYY-MM-DD") D_AUTH_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_AUTH_TIME = NULL('        ');
  string(2) V_RESPONSE_CODE = NULL('  ');
  string(4) V_POS_ENTRY_MODE = NULL('    ');
  string(3) V_SERVICE_CODE = NULL('   ');
  string(3) V_ECI_MOTO_IND = NULL('   ');
  string(2) V_TERMINAL_CAPABILITY = NULL('  ');
  string(40) V_CREATE_USER = NULL('                                        ');
  string(30) V_CASE_STATUS_DESC = NULL('                              ');
  string(40) V_ANALYST_NAME = NULL('                                        ');
  string(1) V_SLA_IND = NULL(' ');
  string(25) V_ROLE_NAME = NULL('                         ');
  string(40) V_RSN_DESC = NULL('                                        ');
  string(80) V_DISP_TYPE_DESC = NULL('                                                                                ');
  string(40) V_BENEFIT_DESC = NULL('                                        ');
  string(10) V_PRODUCT_TYPE = NULL('          ');
  string(40) V_PRODUCT_DESC = NULL('                                        ');
  string(19) V_CUST_NBR = NULL('                   ');
  string(170) V_CUST_NAME = NULL('                                                                                                                                                                          ');
  string(15) V_CONTACT_NUM = NULL('               ');
  string(19) V_ACCT_NBR = NULL('                   ');
  string(10) V_PULL_SESSION_NBR = NULL('          ');
  string(40) V_DEPT_DESC = NULL('                                        ');
  string(10) V_BENEFIT_APP_DATE = NULL('          ');
  string(300) V_BDADSDWO_INI_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(300) V_BDADSDWO_CLS_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(15) V_BDADSDWO_MERCHANT_CITY = NULL('               ');
  string(15) V_BDADSDWO_CASE_FAV_AGAINST = NULL('               ');
  string(1) V_BDADSDWO_RECATIVE_IND = NULL(' ');
  string(15) V_BDADSDWO_PREV_CASE_NBR = NULL('               ');
  string(50) V_BDADSDWO_CONDUSEF_CNBR = NULL('                                                  ');
  string(4) V_BDADSDWO_ADSCTLG_RULE_NO = NULL('    ');
  string(40) V_BDADSDWO_ADSCTLG_RULE_DESC = NULL('                                        ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_SIRH = NULL('               ');
  string(15) V_BDADSDWO_CUS_SEG_ID = NULL('               ');
  string(19) V_DPAN_ACCT_NBR = NULL('                   ');
  string(1) V_WALLET_TXN_TOKEN_IND_CDE = NULL(' ');
  string(17) V_MT_WRITEOFF = NULL('                 ');
  string(4) V_ACCT_BRANCH_OPEN = NULL('    ');
  decimal(12) N_CONTRACT_NO = NULL('            ');
  date("YYYY-MM-DD") D_CANCEL_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_ACCT_STA_FLG = NULL(' ');
  string(4) V_ACCT_RESTR = NULL('    ');
  string(4) V_SUB_PROD_TY_CD = NULL('    ');
  string(1) V_SOURCE_TXN = NULL(' ');
  string(40) V_TRANS_DESC = NULL('                                        ');
  decimal(12) N_CHECK_NBR = NULL('            ');
  string(4) V_TXN_BRANCH = NULL('    ');
  string(2) V_BRANCH_CASH = NULL('  ');
  string(4) V_WFLOW_BRANCH = NULL('    ');
  string(8) V_WFLOW_SIRH = NULL('        ');
  string(3) V_CLIAM_ORIG = NULL('   ');
  decimal(12) N_WRITEOFF_AMT = NULL('            ');
  decimal(4) N_ADJ_REJ_CDE = NULL('    ');
  string(1) V_PAY_TYPE_CDE = NULL(' ');
  date("YYYY-MM-DD") D_CUTOFF_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(19) V_ADJ_ACCT = NULL('                   ');
  string(40) V_BENIF_NAME = NULL('                                        ');
  string(19) V_NON_CUS_NBR = NULL('                   ');
  string(20) V_PYMT_CONT_NBR = NULL('                    ');
  date("YYYY-MM-DD") D_POC_ISSUE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  date("YYYY-MM-DD") D_POC_PAY_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_POC_BRANCH = NULL('    ');
  date("YYYY-MM-DD") D_COMM_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(2) V_COMM_MODE = NULL('  ');
  string(40) V_CUST_STREET_NO = NULL('                                        ');
  string(25) V_CUST_CITY = NULL('                         ');
  string(20) V_CUST_STATE = NULL('                    ');
  decimal(6) N_CUST_ZIP_CODE = NULL('      ');
  decimal(15) N_CUST_PHONE = NULL('               ');
  string(40) V_CUST_MAIL = NULL('                                        ');
  decimal(4) N_TXN_APP_ID = NULL('    ');
  date("YYYY-MM-DD") D_EST_RES_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(27) V_PROB_FACTOR = NULL('                           ');
  decimal(2) N_SCORE_ERRCD = NULL('  ');
  decimal(17) N_DISP_AMT_LC = NULL('                 ');
  string(3) V_VCR_DISPUTE_CATEGORY = NULL('   ');
  string(6) V_VCR_DISP_STATUS = NULL('      ');
  string(1) V_VCR_IO_IND = NULL(' ');
  string(10) V_VISA_CASE_NBR = NULL('          ');
  string(11) V_VISA_FINANCIAL_ID = NULL('           ');
  string(9) V_QUICK_FORM_ID = NULL('         ');
  string(10) V_QUICK_FORM_TYPE = NULL('          ');
  string(100) V_VCR_CASE_STATUS = NULL('                                                                                                    ');
  string(15) V_FRD_CASE_NBR = NULL('               ');
  string(15) V_PRCL_CASE_NBR = NULL('               ');
  string(20) V_NETWORK_ID = NULL('                    ');
  string(20) V_INTL_ID_ATTR = NULL('                    ');
  string(20) V_INTL_ID_TRN_ATTR = NULL('                    ');
  string(10) V_FOLLOW_UP_DT = NULL('          ');
  decimal(4) N_DAYS_TO_ACT = NULL('    ');
  string(10) V_DATE_TO_RSP = NULL('          ');
  string(10) V_LAST_ACTION_DT = NULL('          ');
  string(20) V_BID_NAME = NULL('                    ');
  string(30) V_JURISDICTION = NULL('                              ');
  string(10) V_DC_CODE = NULL('          ');
  string(40) V_VCR_ACTION = NULL('                                        ');
  string(3) V_DISP_JURSDC_ATTR = NULL('   ');
  decimal(9) N_DISP_PREARB_ID = NULL('         ');
  string(8) V_PREARB_DISP_CAT = NULL('        ');
  string(6) V_DISPUTE_CONDITION = NULL('      ');
  string(1) V_FRAUD_TYPE = NULL(' ');
  date("YYYY-MM-DD") MIS_DATE =NULL('');
  string(1) V_BNPL_IND  = NULL(' ');
  string(19) V_CLAIM_ID = NULL('                   ');
  string(8) V_CLAIM_TYPE = NULL('        ');
  string(12) V_RETRIEVAL_ID = NULL('            ');
  string(12) V_CHARGEBACK_ID = NULL('            ');
  string(30) V_CHARGEBACK_TYPE = NULL('                              ');
  string(12) V_FRAUD_ID = NULL('            ');
  string(12) V_FEE_ID = NULL('            ');
  string(3) V_AUTH_INDICATORS_CHP = NULL('   ');
  string(3) V_AUTH_INDICATORS_ATM = NULL('   ');
  string(3) V_AUTH_INDICATORS_3DS = NULL('   ');
  string(3) V_AUTH_INDICATORS_CV2 = NULL('   ');
  string(3) V_AUTH_INDICATORS_2FA = NULL('   ');
  string(3) V_AUTH_INDICATORS_WLL = NULL('   ');
  decimal(11) N_MDES_TOKEN_REQID = NULL('           ');
  string(2) N_MDES_TOKEN_B026 = NULL('  ');
  string(1) V_MDES_TOKEN_B027 = NULL(' ');
  decimal(2) N_MDES_TOKEN_ASURLVL = NULL('  ');
  string(2) V_MDES_TKNSTR_TYP = NULL('  ');
  string(2) N_MDES_PREVAL_IND = NULL('  ');
  string(1) V_MDES_PREVAL_RSLT = NULL(' ');
  decimal(3) V_MDES_DSRP_TRAN_ID = NULL('   ');
  string(3) V_CUST_CELL_PHN_SRC = NULL('   ');
  string(3) V_CUST_MAIL_SRC = NULL('   ');
  string(1) V_3DS2_PGM_PROTO = NULL(' ');
  string(1) V_3DS2_EC_3DS_IND = NULL(' ');
  string(36) V_3DS2_DS_TXN_ID = NULL('                                    ');
  string(1) V_3DS2_IAV_PRS_IND = NULL(' ');
  string(1) V_3DS2_IAV_VL_RLT = NULL(' ');
  string(50) V_NCE_IP_INIT = NULL('                                                  ');
  string(20) V_NCE_MAC_ORIGIN = NULL('                    ');
  string(40) V_CUS_SEG_NAME = NULL('                                        ');
  decimal(4) N_ORIG_DBT_TRNS_CD = NULL('    ');
  date("YYYY-MM-DD") V_REACTV_DATE = NULL('');
  string(4) V_REJ_CODE = NULL('    ');
  string(48) V_REJ_DESC = NULL('                                                ');
  string(1) V_WLL_CRYPTOGRAM = NULL(' ');
  string(16) V_ARQC_CRYPTOGRAM = NULL('                ');
  string(2) V_ARQC_VALID_IND = NULL('  ');
  string(20) V_MERCHANT_STATE_NAME = NULL('                    ');
  string(23) V_NUM_REFADQUIRENTE = NULL('                       ');
  date('YYYY-MM-DD') D_FECHA_COMPRA = NULL("");
  decimal(13,2) N_IMP_TRNMONDESTINO =NULL('             ');
  string(50) V_TYPE_REFOUND = NULL('                                                  ');
  decimal(4) N_HIERARCHY =  NULL('    ');
  string("\\n") V_FILLER = NULL('');
  end;|3|1|l|@{0|}}
{30001002|XXparameter|mode|0x0062|3|2|$|@{0|}}
{30001002|XXparameter|Layout|/fct/ecscards/SECS000u13.BBD.DNLOAD.DWH.ADS.EP.20270927_New|3|2|$|@{0|}}
}}@0|Input File|720000|250000|0|0|0|0|169|Input File-2|Ab Initio Software|@1|1000|-1||6||33025|-1|-1|}}
{2010202004|XXGiport|42|0|105|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|43|0|108|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0001|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|create_directories|False|13|1|FKl|If True, create any parent directories as necessary|{0|}}
{30001002|XXparameter|create_directories.display_name|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.keyword|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.condition|version 4.1.1.r9.0:|3|15|P?|@{0|}}
{30001002|XXparameter|translate_format|False|13|1|Fl|If true, translate the file format.|{0|}}
{30001002|XXparameter|translate_format.condition|version 4.0.0.r1.0:|3|15|P?|@{0|}}
{30001002|XXparameter|format|uninterpreted|15|1|FKl|'uninterpreted' (raw data), 'seqfile' (Hadoop sequence file), 'parquet' (Parquet format), 'orc' (ORC format), 'avro' (Avro format), 'texttable' (Hive text table).|{6|uninterpreted|seqfile|parquet|orc|avro|texttable|}}
{30001002|XXparameter|format.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoopy_condition|value format uninterpreted False value format * True default constant False|13|13|Hv|Hidden condition for deciding hadoop-codec visibility|{0|}}
{30001002|XXparameter|hadoopy_condition.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoop_codec|Uncompressed|15|1|FKl|Compression for writing hadoop specific file format. orc=\{ZLIB,SNAPPY,LZO\}, parquet=\{GZIP,SNAPPY,LZO\}, seqfile=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZO\}, avro=\{SNAPPY,Deflate,BZIP2\}, texttable=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4\}|{8|Uncompressed|GZIP|SNAPPY|Deflate|BZIP2|ZLIB|LZ4|LZO|}}
{30001002|XXparameter|hadoop_codec.display_name|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.keyword|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.condition|param_exact hadoopy_condition True param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed only_last_key_instance orc_file|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url||28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|either_or|value block_compressed True True sameas keep_on_disk default constant True|13|13|v|Either B-C or K-o-D|{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if the block compressed lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|mode lookup version 2.15.5.r34: param_exact either_or True|3|15|P?|@{0|}}
{30001002|XXparameter|only_last_key_instance|False|13|1|Fl|Match only the last instance of each key|{0|}}
{30001002|XXparameter|only_last_key_instance.condition|mode lookup version 3.0.2.r12.0:|3|15|P?|@{0|}}
{30001002|XXparameter|orc_file|False|13|1|Fl|Set to true if it is Hive ORC file|{0|}}
{30001002|XXparameter|orc_file.condition|mode lookup version 3.2.2.r15.0: param_exact direct_addressed True param_exact block_compressed False|3|15|P?|@{0|}}
{30001002|XXparameter|Layout||28|2|RF$||{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
{30001002|XXparameter|mpcmodtime|1649796511|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|write_metadata||7|1|RFsl||{0|}}
}}@0|Input File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010202004|XXGiport|44|0|110|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010501005|XXGpvertex|45|0|115|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Dedup_Sorted.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|key|\{\}|3|2|$|@{0|}}
{30001002|XXparameter|dup_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Dedup Sorted|137000|196000|0|0|0|0|175|Dedup Sorted|Ab Initio Software|Built-in 2.0:|1|100|0||6||1|1|{1|0|}}}
{2010203004|XXGoport|46|0|117|0|{@{}@0|0|0|0|out|0.0|@@@2196|0|}}
{2010203004|XXGoport|47|0|120|0|{@{}@0|0|0|0|dup|0.0|@@@2192|0|}}
{2010203004|XXGoport|48|0|123|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|49|0|125|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|50|0|127|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|51|0|129|0|{@{}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|52|0|132|0|{Separates one specified data record in each group of data records from the rest of the records in the group.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|dedup|3|1|Hl||{0|}}
{30001002|XXparameter|image__|/~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|key||19|2|RFO$|Key on which to remove duplicates|{0|}}
{30001002|XXparameter|select||20|2|FK$|Optional select expression|{0|}}
{30001002|XXparameter|keep|first|15|1|FKl|Output record for a group of duplicates|{3|first|last|unique-only|}}
{30001002|XXparameter|package||8|1|FKl|Package containing transforms and data types|{0|}}
{30001002|XXparameter|package.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version :2.12.999.m999|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword2|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword2.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp ramp_keyword2 ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|check_sort|True|13|1|FKl|Abort on first record that is out of sorted order|{0|}}
{30001002|XXparameter|check_sort.display_name|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.keyword|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.condition|version 2.11.1:|3|15|P?|@{0|}}
{30001002|XXparameter|check_sort.update_clauses|update_value False|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|NoHidePorts|out|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|reject=in; out=in; dup=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select); dup=filter(select)|3|2|H$||{0|}}
{30001002|XXparameter|num_types|2|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation1|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation2|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation3|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|num_operations|4|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|num_callbacks|4|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|dup_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,dup,reject,error,log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1649796515|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: dup = in
metadata type: in = out
metadata type: in = dup|3|1|FHKl|@{0|}}
}}@0|Dedup Sorted|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|53|0|134|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2196|0|}}
{2010203004|XXGoport|54|0|137|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|dup|0.0|@@@2192|0|}}
{2010203004|XXGoport|55|0|140|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|56|0|143|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|57|0|146|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|58|0|149|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010503005|XXGfvertex|59|0|153|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|read_metadata|// banamex/sr610891/111618/ADS_D.dml
// Schema File DML Generated: 2018-12-11 15:45:05 Version: 13269
type rec_t =
record
  string(1) V_REC_TYPE = NULL(' ');
  date("YYYY-MM-DD") D_PROCESS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(11) V_CASE_NBR = NULL('           ');
  string(23) V_ACQ_REF_NBR = NULL('                       ');
  string(19) V_CARD_NBR = NULL('                   ');
  string(3) V_ORG = NULL('   ');
  string(3) V_LOGO = NULL('   ');
  date("YYYY-MM-DD") D_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_STATUS = NULL(' ');
  date("YYYY-MM-DD") D_TRANS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_TRANS_CD = NULL('    ');
  decimal(12) N_ORIG_TRANS_AMT = NULL('            ');
  decimal(2) N_ORIG_TRANS_AMT_EXP = NULL('  ');
  decimal(4) N_ORIG_CURR_CD = NULL('    ');
  string(16) V_MERCH_ID = NULL('                ');
  string(4) V_MCC = NULL('    ');
  string(8) V_UPDATE_USERID = NULL('        ');
  date("YYYY-MM-DD") D_CREATE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(12) N_DISP_AMT = NULL('            ');
  decimal(2) N_DISP_AMT_EXP = NULL('  ');
  decimal(4) N_DISP_CURR_CD = NULL('    ');
  decimal(4) N_REASON_CD = NULL('    ');
  string(25) V_MERCH_NAME = NULL('                         ');
  string(3) V_MERCH_CNTRY = NULL('   ');
  string(5) V_IWI_INSTALL_NBR = NULL('     ');
  string(8) V_AUTH_CODE = NULL('        ');
  string(2) V_POS_MODE = NULL('  ');
  decimal(3) N_ECMMRCE_IND = NULL('   ');
  string(3) V_CASE_STATUS = NULL('   ');
  string(8) V_ASSIGNED_TO = NULL('        ');
  string(3) V_DISP_TYPE = NULL('   ');
  decimal(4) N_CLS_RSN_CD = NULL('    ');
  decimal(4) N_INIT_RSN_CD = NULL('    ');
  string(30) V_REMARKS = NULL('                              ');
  decimal(12) N_TRAN_TYPE = NULL('            ');
  string(10) V_SETTLEMENT_DATE = NULL('          ');
  string(20) V_MMT = NULL('                    ');
  decimal(1) N_DOC_IND = NULL(' ');
  decimal(6) N_PLAN = NULL('      ');
  string(3) V_MOD_ID = NULL('   ');
  string(6) V_LV = NULL('      ');
  string(1) V_TCR_E = NULL(' ');
  string(15) V_CLAIM_NBR = NULL('               ');
  string(3) V_PRIOR_CASE_STATUS = NULL('   ');
  string(1) V_SHIELD_IDENTIFICATION = NULL(' ');
  string(2) V_ACCT_STATUS = NULL('  ');
  string(12) V_UPDATE_TIME = NULL('            ');
  string(8) V_CREATE_USER_ID = NULL('        ');
  string(25) V_GROUP_DESC = NULL('                         ');
  string(8) V_GROUP_ID = NULL('        ');
  string(1) V_CARD_BLOCK_CODE = NULL(' ');
  string(2) V_CARD_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_CARD_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_CARD_BLOCK_TIME = NULL('        ');
  string(4) V_ACCT_BLOCK_CODE = NULL('    ');
  string(2) V_ACCT_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_ACCT_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_ACCT_BLOCK_TIME = NULL('        ');
  string(4) V_CHANNEL = NULL('    ');
  date("YYYY-MM-DD") D_AUTH_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_AUTH_TIME = NULL('        ');
  string(2) V_RESPONSE_CODE = NULL('  ');
  string(4) V_POS_ENTRY_MODE = NULL('    ');
  string(3) V_SERVICE_CODE = NULL('   ');
  string(3) V_ECI_MOTO_IND = NULL('   ');
  string(2) V_TERMINAL_CAPABILITY = NULL('  ');
  string(40) V_CREATE_USER = NULL('                                        ');
  string(30) V_CASE_STATUS_DESC = NULL('                              ');
  string(40) V_ANALYST_NAME = NULL('                                        ');
  string(1) V_SLA_IND = NULL(' ');
  string(25) V_ROLE_NAME = NULL('                         ');
  string(40) V_RSN_DESC = NULL('                                        ');
  string(80) V_DISP_TYPE_DESC = NULL('                                                                                ');
  string(40) V_BENEFIT_DESC = NULL('                                        ');
  string(10) V_PRODUCT_TYPE = NULL('          ');
  string(40) V_PRODUCT_DESC = NULL('                                        ');
  string(19) V_CUST_NBR = NULL('                   ');
  string(170) V_CUST_NAME = NULL('                                                                                                                                                                          ');
  string(15) V_CONTACT_NUM = NULL('               ');
  string(19) V_ACCT_NBR = NULL('                   ');
  string(10) V_PULL_SESSION_NBR = NULL('          ');
  string(40) V_DEPT_DESC = NULL('                                        ');
  string(10) V_BENEFIT_APP_DATE = NULL('          ');
  string(300) V_BDADSDWO_INI_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(300) V_BDADSDWO_CLS_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(15) V_BDADSDWO_MERCHANT_CITY = NULL('               ');
  string(15) V_BDADSDWO_CASE_FAV_AGAINST = NULL('               ');
  string(1) V_BDADSDWO_RECATIVE_IND = NULL(' ');
  string(15) V_BDADSDWO_PREV_CASE_NBR = NULL('               ');
  string(50) V_BDADSDWO_CONDUSEF_CNBR = NULL('                                                  ');
  string(4) V_BDADSDWO_ADSCTLG_RULE_NO = NULL('    ');
  string(40) V_BDADSDWO_ADSCTLG_RULE_DESC = NULL('                                        ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_SIRH = NULL('               ');
  string(15) V_BDADSDWO_CUS_SEG_ID = NULL('               ');
  string(19) V_DPAN_ACCT_NBR = NULL('                   ');
  string(1) V_WALLET_TXN_TOKEN_IND_CDE = NULL(' ');
  string(17) V_MT_WRITEOFF = NULL('                 ');
  string(4) V_ACCT_BRANCH_OPEN = NULL('    ');
  decimal(12) N_CONTRACT_NO = NULL('            ');
  date("YYYY-MM-DD") D_CANCEL_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_ACCT_STA_FLG = NULL(' ');
  string(4) V_ACCT_RESTR = NULL('    ');
  string(4) V_SUB_PROD_TY_CD = NULL('    ');
  string(1) V_SOURCE_TXN = NULL(' ');
  string(40) V_TRANS_DESC = NULL('                                        ');
  decimal(12) N_CHECK_NBR = NULL('            ');
  string(4) V_TXN_BRANCH = NULL('    ');
  string(2) V_BRANCH_CASH = NULL('  ');
  string(4) V_WFLOW_BRANCH = NULL('    ');
  string(8) V_WFLOW_SIRH = NULL('        ');
  string(3) V_CLIAM_ORIG = NULL('   ');
  decimal(12) N_WRITEOFF_AMT = NULL('            ');
  decimal(4) N_ADJ_REJ_CDE = NULL('    ');
  string(1) V_PAY_TYPE_CDE = NULL(' ');
  date("YYYY-MM-DD") D_CUTOFF_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(19) V_ADJ_ACCT = NULL('                   ');
  string(40) V_BENIF_NAME = NULL('                                        ');
  string(19) V_NON_CUS_NBR = NULL('                   ');
  string(20) V_PYMT_CONT_NBR = NULL('                    ');
  date("YYYY-MM-DD") D_POC_ISSUE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  date("YYYY-MM-DD") D_POC_PAY_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_POC_BRANCH = NULL('    ');
  date("YYYY-MM-DD") D_COMM_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(2) V_COMM_MODE = NULL('  ');
  string(40) V_CUST_STREET_NO = NULL('                                        ');
  string(25) V_CUST_CITY = NULL('                         ');
  string(20) V_CUST_STATE = NULL('                    ');
  decimal(6) N_CUST_ZIP_CODE = NULL('      ');
  decimal(15) N_CUST_PHONE = NULL('               ');
  string(40) V_CUST_MAIL = NULL('                                        ');
  decimal(4) N_TXN_APP_ID = NULL('    ');
  date("YYYY-MM-DD") D_EST_RES_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(27) V_PROB_FACTOR = NULL('                           ');
  decimal(2) N_SCORE_ERRCD = NULL('  ');
  decimal(17) N_DISP_AMT_LC = NULL('                 ');
  string(3) V_VCR_DISPUTE_CATEGORY = NULL('   ');
  string(6) V_VCR_DISP_STATUS = NULL('      ');
  string(1) V_VCR_IO_IND = NULL(' ');
  string(10) V_VISA_CASE_NBR = NULL('          ');
  string(11) V_VISA_FINANCIAL_ID = NULL('           ');
  string(9) V_QUICK_FORM_ID = NULL('         ');
  string(10) V_QUICK_FORM_TYPE = NULL('          ');
  string(100) V_VCR_CASE_STATUS = NULL('                                                                                                    ');
  string(15) V_FRD_CASE_NBR = NULL('               ');
  string(15) V_PRCL_CASE_NBR = NULL('               ');
  string(20) V_NETWORK_ID = NULL('                    ');
  string(20) V_INTL_ID_ATTR = NULL('                    ');
  string(20) V_INTL_ID_TRN_ATTR = NULL('                    ');
  string(10) V_FOLLOW_UP_DT = NULL('          ');
  decimal(4) N_DAYS_TO_ACT = NULL('    ');
  string(10) V_DATE_TO_RSP = NULL('          ');
  string(10) V_LAST_ACTION_DT = NULL('          ');
  string(20) V_BID_NAME = NULL('                    ');
  string(30) V_JURISDICTION = NULL('                              ');
  string(10) V_DC_CODE = NULL('          ');
  string(40) V_VCR_ACTION = NULL('                                        ');
  string(3) V_DISP_JURSDC_ATTR = NULL('   ');
  decimal(9) N_DISP_PREARB_ID = NULL('         ');
  string(8) V_PREARB_DISP_CAT = NULL('        ');
  string(6) V_DISPUTE_CONDITION = NULL('      ');
  string(1) V_FRAUD_TYPE = NULL(' ');
  date("YYYY-MM-DD") MIS_DATE =NULL('');
  string(1) V_BNPL_IND  = NULL(' ');
  string(2) V_CHIP_PIN_IND = NULL('  '); /*filler field*/
  string(19) V_CLAIM_ID = NULL('                   ');
  string(8) V_CLAIM_TYPE = NULL('        ');
  string(12) V_RETRIEVAL_ID = NULL('            ');
  string(12) V_CHARGEBACK_ID = NULL('            ');
  string(30) V_CHARGEBACK_TYPE = NULL('                              ');
  string(12) V_FRAUD_ID = NULL('            ');
  string(12) V_FEE_ID = NULL('            ');
  string(3) V_AUTH_INDICATORS_CHP = NULL('   ');
  string(3) V_AUTH_INDICATORS_ATM = NULL('   ');
  string(3) V_AUTH_INDICATORS_3DS = NULL('   ');
  string(3) V_AUTH_INDICATORS_CV2 = NULL('   ');
  string(3) V_AUTH_INDICATORS_2FA = NULL('   ');
  string(3) V_AUTH_INDICATORS_WLL = NULL('   ');
  decimal(11) N_MDES_TOKEN_REQID = NULL('           ');
  string(2) N_MDES_TOKEN_B026 = NULL('  ');
  string(1) V_MDES_TOKEN_B027 = NULL(' ');
  decimal(2) N_MDES_TOKEN_ASURLVL = NULL('  ');
  string(2) V_MDES_TKNSTR_TYP = NULL('  ');
  string(2) N_MDES_PREVAL_IND = NULL('  ');
  string(1) V_MDES_PREVAL_RSLT = NULL(' ');
  decimal(3) V_MDES_DSRP_TRAN_ID = NULL('   ');
  string(3) V_CUST_CELL_PHN_SRC = NULL('   ');
  string(3) V_CUST_MAIL_SRC = NULL('   ');
  string(1) V_3DS2_PGM_PROTO = NULL(' ');
  string(1) V_3DS2_EC_3DS_IND = NULL(' ');
  string(36) V_3DS2_DS_TXN_ID = NULL('                                    ');
  string(1) V_3DS2_IAV_PRS_IND = NULL(' ');
  string(1) V_3DS2_IAV_VL_RLT = NULL(' ');
  string(15) V_NCE_IP_INIT = NULL('               ');
  string(17) V_NCE_MAC_ORIGIN = NULL('                 ');
  string(40) V_CUS_SEG_NAME = NULL('                                        ');
  decimal(4) N_ORIG_DBT_TRNS_CD = NULL('    ');
  date("YYYY-MM-DD") V_REACTV_DATE = NULL('');
  string(4) V_REJ_CODE = NULL('    ');
  string(48) V_REJ_DESC = NULL('                                                ');
  string(1) V_WLL_CRYPTOGRAM = NULL(' ');
  string(16) V_ARQC_CRYPTOGRAM = NULL('                ');
  string(2) V_ARQC_VALID_IND = NULL('  ');
  string(20) V_MERCHANT_STATE_NAME = NULL('                    ');
  string(23) V_NUM_REFADQUIRENTE = NULL('                       ');
  date('YYYY-MM-DD') D_FECHA_COMPRA = NULL("");
  decimal(13,2) N_IMP_TRNMONDESTINO =NULL('             ');
  string(50) V_TYPE_REFOUND = NULL('                                                  ');
  decimal(4) N_HIERARCHY =  NULL('    ');
  string("\\n") V_FILLER = NULL('');
  end;
metadata type = 
record
  string(1) V_REC_TYPE = NULL(' ');
  date("YYYY-MM-DD") D_PROCESS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(11) V_CASE_NBR = NULL('           ');
  string(23) V_ACQ_REF_NBR = NULL('                       ');
  string(19) V_CARD_NBR = NULL('                   ');
  string(3) V_ORG = NULL('   ');
  string(3) V_LOGO = NULL('   ');
  date("YYYY-MM-DD") D_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_STATUS = NULL(' ');
  date("YYYY-MM-DD") D_TRANS_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_TRANS_CD = NULL('    ');
  decimal(12) N_ORIG_TRANS_AMT = NULL('            ');
  decimal(2) N_ORIG_TRANS_AMT_EXP = NULL('  ');
  decimal(4) N_ORIG_CURR_CD = NULL('    ');
  string(16) V_MERCH_ID = NULL('                ');
  string(4) V_MCC = NULL('    ');
  string(8) V_UPDATE_USERID = NULL('        ');
  date("YYYY-MM-DD") D_CREATE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(12) N_DISP_AMT = NULL('            ');
  decimal(2) N_DISP_AMT_EXP = NULL('  ');
  decimal(4) N_DISP_CURR_CD = NULL('    ');
  decimal(4) N_REASON_CD = NULL('    ');
  string(25) V_MERCH_NAME = NULL('                         ');
  string(3) V_MERCH_CNTRY = NULL('   ');
  string(5) V_IWI_INSTALL_NBR = NULL('     ');
  string(8) V_AUTH_CODE = NULL('        ');
  string(2) V_POS_MODE = NULL('  ');
  decimal(3) N_ECMMRCE_IND = NULL('   ');
  string(3) V_CASE_STATUS = NULL('   ');
  string(8) V_ASSIGNED_TO = NULL('        ');
  string(3) V_DISP_TYPE = NULL('   ');
  decimal(4) N_CLS_RSN_CD = NULL('    ');
  decimal(4) N_INIT_RSN_CD = NULL('    ');
  string(30) V_REMARKS = NULL('                              ');
  decimal(12) N_TRAN_TYPE = NULL('            ');
  string(10) V_SETTLEMENT_DATE = NULL('          ');
  string(20) V_MMT = NULL('                    ');
  decimal(1) N_DOC_IND = NULL(' ');
  decimal(6) N_PLAN = NULL('      ');
  string(3) V_MOD_ID = NULL('   ');
  string(6) V_LV = NULL('      ');
  string(1) V_TCR_E = NULL(' ');
  string(15) V_CLAIM_NBR = NULL('               ');
  string(3) V_PRIOR_CASE_STATUS = NULL('   ');
  string(1) V_SHIELD_IDENTIFICATION = NULL(' ');
  string(2) V_ACCT_STATUS = NULL('  ');
  string(12) V_UPDATE_TIME = NULL('            ');
  string(8) V_CREATE_USER_ID = NULL('        ');
  string(25) V_GROUP_DESC = NULL('                         ');
  string(8) V_GROUP_ID = NULL('        ');
  string(1) V_CARD_BLOCK_CODE = NULL(' ');
  string(2) V_CARD_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_CARD_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_CARD_BLOCK_TIME = NULL('        ');
  string(4) V_ACCT_BLOCK_CODE = NULL('    ');
  string(2) V_ACCT_BLOCK_RSN_CDE = NULL('  ');
  date("YYYY-MM-DD") D_ACCT_BLOCK_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_ACCT_BLOCK_TIME = NULL('        ');
  string(4) V_CHANNEL = NULL('    ');
  date("YYYY-MM-DD") D_AUTH_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(8) V_AUTH_TIME = NULL('        ');
  string(2) V_RESPONSE_CODE = NULL('  ');
  string(4) V_POS_ENTRY_MODE = NULL('    ');
  string(3) V_SERVICE_CODE = NULL('   ');
  string(3) V_ECI_MOTO_IND = NULL('   ');
  string(2) V_TERMINAL_CAPABILITY = NULL('  ');
  string(40) V_CREATE_USER = NULL('                                        ');
  string(30) V_CASE_STATUS_DESC = NULL('                              ');
  string(40) V_ANALYST_NAME = NULL('                                        ');
  string(1) V_SLA_IND = NULL(' ');
  string(25) V_ROLE_NAME = NULL('                         ');
  string(40) V_RSN_DESC = NULL('                                        ');
  string(80) V_DISP_TYPE_DESC = NULL('                                                                                ');
  string(40) V_BENEFIT_DESC = NULL('                                        ');
  string(10) V_PRODUCT_TYPE = NULL('          ');
  string(40) V_PRODUCT_DESC = NULL('                                        ');
  string(19) V_CUST_NBR = NULL('                   ');
  string(170) V_CUST_NAME = NULL('                                                                                                                                                                          ');
  string(15) V_CONTACT_NUM = NULL('               ');
  string(19) V_ACCT_NBR = NULL('                   ');
  string(10) V_PULL_SESSION_NBR = NULL('          ');
  string(40) V_DEPT_DESC = NULL('                                        ');
  string(10) V_BENEFIT_APP_DATE = NULL('          ');
  string(300) V_BDADSDWO_INI_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(300) V_BDADSDWO_CLS_MEMO_TEXT = NULL('                                                                                                                                                                                                                                                                                                            ');
  string(15) V_BDADSDWO_MERCHANT_CITY = NULL('               ');
  string(15) V_BDADSDWO_CASE_FAV_AGAINST = NULL('               ');
  string(1) V_BDADSDWO_RECATIVE_IND = NULL(' ');
  string(15) V_BDADSDWO_PREV_CASE_NBR = NULL('               ');
  string(50) V_BDADSDWO_CONDUSEF_CNBR = NULL('                                                  ');
  string(4) V_BDADSDWO_ADSCTLG_RULE_NO = NULL('    ');
  string(40) V_BDADSDWO_ADSCTLG_RULE_DESC = NULL('                                        ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_1 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_ACCT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_PROD_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_CR_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_GL_DB_DEPT_NBR_2 = NULL('               ');
  string(15) V_BDADSDWO_SIRH = NULL('               ');
  string(15) V_BDADSDWO_CUS_SEG_ID = NULL('               ');
  string(19) V_DPAN_ACCT_NBR = NULL('                   ');
  string(1) V_WALLET_TXN_TOKEN_IND_CDE = NULL(' ');
  string(17) V_MT_WRITEOFF = NULL('                 ');
  string(4) V_ACCT_BRANCH_OPEN = NULL('    ');
  decimal(12) N_CONTRACT_NO = NULL('            ');
  date("YYYY-MM-DD") D_CANCEL_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(1) V_ACCT_STA_FLG = NULL(' ');
  string(4) V_ACCT_RESTR = NULL('    ');
  string(4) V_SUB_PROD_TY_CD = NULL('    ');
  string(1) V_SOURCE_TXN = NULL(' ');
  string(40) V_TRANS_DESC = NULL('                                        ');
  decimal(12) N_CHECK_NBR = NULL('            ');
  string(4) V_TXN_BRANCH = NULL('    ');
  string(2) V_BRANCH_CASH = NULL('  ');
  string(4) V_WFLOW_BRANCH = NULL('    ');
  string(8) V_WFLOW_SIRH = NULL('        ');
  string(3) V_CLIAM_ORIG = NULL('   ');
  decimal(12) N_WRITEOFF_AMT = NULL('            ');
  decimal(4) N_ADJ_REJ_CDE = NULL('    ');
  string(1) V_PAY_TYPE_CDE = NULL(' ');
  date("YYYY-MM-DD") D_CUTOFF_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(19) V_ADJ_ACCT = NULL('                   ');
  string(40) V_BENIF_NAME = NULL('                                        ');
  string(19) V_NON_CUS_NBR = NULL('                   ');
  string(20) V_PYMT_CONT_NBR = NULL('                    ');
  date("YYYY-MM-DD") D_POC_ISSUE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  date("YYYY-MM-DD") D_POC_PAY_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  decimal(4) N_POC_BRANCH = NULL('    ');
  date("YYYY-MM-DD") D_COMM_CLOSE_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(2) V_COMM_MODE = NULL('  ');
  string(40) V_CUST_STREET_NO = NULL('                                        ');
  string(25) V_CUST_CITY = NULL('                         ');
  string(20) V_CUST_STATE = NULL('                    ');
  decimal(6) N_CUST_ZIP_CODE = NULL('      ');
  decimal(15) N_CUST_PHONE = NULL('               ');
  string(40) V_CUST_MAIL = NULL('                                        ');
  decimal(4) N_TXN_APP_ID = NULL('    ');
  date("YYYY-MM-DD") D_EST_RES_DATE = NULL('') /* vector of null vals '0000000000,          ,9999999999,0000-00-00,9999-99-99'*/;
  string(27) V_PROB_FACTOR = NULL('                           ');
  decimal(2) N_SCORE_ERRCD = NULL('  ');
  decimal(17) N_DISP_AMT_LC = NULL('                 ');
  string(3) V_VCR_DISPUTE_CATEGORY = NULL('   ');
  string(6) V_VCR_DISP_STATUS = NULL('      ');
  string(1) V_VCR_IO_IND = NULL(' ');
  string(10) V_VISA_CASE_NBR = NULL('          ');
  string(11) V_VISA_FINANCIAL_ID = NULL('           ');
  string(9) V_QUICK_FORM_ID = NULL('         ');
  string(10) V_QUICK_FORM_TYPE = NULL('          ');
  string(100) V_VCR_CASE_STATUS = NULL('                                                                                                    ');
  string(15) V_FRD_CASE_NBR = NULL('               ');
  string(15) V_PRCL_CASE_NBR = NULL('               ');
  string(20) V_NETWORK_ID = NULL('                    ');
  string(20) V_INTL_ID_ATTR = NULL('                    ');
  string(20) V_INTL_ID_TRN_ATTR = NULL('                    ');
  string(10) V_FOLLOW_UP_DT = NULL('          ');
  decimal(4) N_DAYS_TO_ACT = NULL('    ');
  string(10) V_DATE_TO_RSP = NULL('          ');
  string(10) V_LAST_ACTION_DT = NULL('          ');
  string(20) V_BID_NAME = NULL('                    ');
  string(30) V_JURISDICTION = NULL('                              ');
  string(10) V_DC_CODE = NULL('          ');
  string(40) V_VCR_ACTION = NULL('                                        ');
  string(3) V_DISP_JURSDC_ATTR = NULL('   ');
  decimal(9) N_DISP_PREARB_ID = NULL('         ');
  string(8) V_PREARB_DISP_CAT = NULL('        ');
  string(6) V_DISPUTE_CONDITION = NULL('      ');
  string(1) V_FRAUD_TYPE = NULL(' ');
  date("YYYY-MM-DD") MIS_DATE =NULL('');
  string(1) V_BNPL_IND  = NULL(' ');
  string(19) V_CLAIM_ID = NULL('                   ');
  string(8) V_CLAIM_TYPE = NULL('        ');
  string(12) V_RETRIEVAL_ID = NULL('            ');
  string(12) V_CHARGEBACK_ID = NULL('            ');
  string(30) V_CHARGEBACK_TYPE = NULL('                              ');
  string(12) V_FRAUD_ID = NULL('            ');
  string(12) V_FEE_ID = NULL('            ');
  string(3) V_AUTH_INDICATORS_CHP = NULL('   ');
  string(3) V_AUTH_INDICATORS_ATM = NULL('   ');
  string(3) V_AUTH_INDICATORS_3DS = NULL('   ');
  string(3) V_AUTH_INDICATORS_CV2 = NULL('   ');
  string(3) V_AUTH_INDICATORS_2FA = NULL('   ');
  string(3) V_AUTH_INDICATORS_WLL = NULL('   ');
  decimal(11) N_MDES_TOKEN_REQID = NULL('           ');
  string(2) N_MDES_TOKEN_B026 = NULL('  ');
  string(1) V_MDES_TOKEN_B027 = NULL(' ');
  decimal(2) N_MDES_TOKEN_ASURLVL = NULL('  ');
  string(2) V_MDES_TKNSTR_TYP = NULL('  ');
  string(2) N_MDES_PREVAL_IND = NULL('  ');
  string(1) V_MDES_PREVAL_RSLT = NULL(' ');
  decimal(3) V_MDES_DSRP_TRAN_ID = NULL('   ');
  string(3) V_CUST_CELL_PHN_SRC = NULL('   ');
  string(3) V_CUST_MAIL_SRC = NULL('   ');
  string(1) V_3DS2_PGM_PROTO = NULL(' ');
  string(1) V_3DS2_EC_3DS_IND = NULL(' ');
  string(36) V_3DS2_DS_TXN_ID = NULL('                                    ');
  string(1) V_3DS2_IAV_PRS_IND = NULL(' ');
  string(1) V_3DS2_IAV_VL_RLT = NULL(' ');
  string(50) V_NCE_IP_INIT = NULL('                                                  ');
  string(20) V_NCE_MAC_ORIGIN = NULL('                    ');
  string(40) V_CUS_SEG_NAME = NULL('                                        ');
  decimal(4) N_ORIG_DBT_TRNS_CD = NULL('    ');
  date("YYYY-MM-DD") V_REACTV_DATE = NULL('');
  string(4) V_REJ_CODE = NULL('    ');
  string(48) V_REJ_DESC = NULL('                                                ');
  string(1) V_WLL_CRYPTOGRAM = NULL(' ');
  string(16) V_ARQC_CRYPTOGRAM = NULL('                ');
  string(2) V_ARQC_VALID_IND = NULL('  ');
  string(20) V_MERCHANT_STATE_NAME = NULL('                    ');
  string(23) V_NUM_REFADQUIRENTE = NULL('                       ');
  date('YYYY-MM-DD') D_FECHA_COMPRA = NULL("");
  decimal(13,2) N_IMP_TRNMONDESTINO =NULL('             ');
  string(50) V_TYPE_REFOUND = NULL('                                                  ');
  decimal(4) N_HIERARCHY =  NULL('    ');
  string("\\n") V_FILLER = NULL('');
  end;|3|1|l|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("read", "pdl") map_dataset 1 mapping [record dataset_path _interp_("/fct/ecscards/SECS000u13.BBD.DNLOAD.DWH.ADS.EP.20270927", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|/fct/ecscards/SECS000u13.BBD.DNLOAD.DWH.ADS.EP.20270927|3|2|$|@{0|}}
}}@0|Input File|15000|215000|0|0|0|0|170|Input File-1|Ab Initio Software|@1|1000|-1||6||33025|-1|-1|}}
{2010203004|XXGoport|60|0|155|0|{@{}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|61|0|158|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0001|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|create_directories|False|13|1|FKl|If True, create any parent directories as necessary|{0|}}
{30001002|XXparameter|create_directories.display_name|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.keyword|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.condition|version 4.1.1.r9.0:|3|15|P?|@{0|}}
{30001002|XXparameter|translate_format|False|13|1|Fl|If true, translate the file format.|{0|}}
{30001002|XXparameter|translate_format.condition|version 4.0.0.r1.0:|3|15|P?|@{0|}}
{30001002|XXparameter|format|uninterpreted|15|1|FKl|'uninterpreted' (raw data), 'seqfile' (Hadoop sequence file), 'parquet' (Parquet format), 'orc' (ORC format), 'avro' (Avro format), 'texttable' (Hive text table).|{6|uninterpreted|seqfile|parquet|orc|avro|texttable|}}
{30001002|XXparameter|format.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoopy_condition|value format uninterpreted False value format * True default constant False|13|13|Hv|Hidden condition for deciding hadoop-codec visibility|{0|}}
{30001002|XXparameter|hadoopy_condition.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoop_codec|Uncompressed|15|1|FKl|Compression for writing hadoop specific file format. orc=\{ZLIB,SNAPPY,LZO\}, parquet=\{GZIP,SNAPPY,LZO\}, seqfile=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZO\}, avro=\{SNAPPY,Deflate,BZIP2\}, texttable=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4\}|{8|Uncompressed|GZIP|SNAPPY|Deflate|BZIP2|ZLIB|LZ4|LZO|}}
{30001002|XXparameter|hadoop_codec.display_name|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.keyword|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.condition|param_exact hadoopy_condition True param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed only_last_key_instance orc_file|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url||28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|either_or|value block_compressed True True sameas keep_on_disk default constant True|13|13|v|Either B-C or K-o-D|{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if the block compressed lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|mode lookup version 2.15.5.r34: param_exact either_or True|3|15|P?|@{0|}}
{30001002|XXparameter|only_last_key_instance|False|13|1|Fl|Match only the last instance of each key|{0|}}
{30001002|XXparameter|only_last_key_instance.condition|mode lookup version 3.0.2.r12.0:|3|15|P?|@{0|}}
{30001002|XXparameter|orc_file|False|13|1|Fl|Set to true if it is Hive ORC file|{0|}}
{30001002|XXparameter|orc_file.condition|mode lookup version 3.2.2.r15.0: param_exact direct_addressed True param_exact block_compressed False|3|15|P?|@{0|}}
{30001002|XXparameter|Layout||28|2|RF$||{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
{30001002|XXparameter|read_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|mpcmodtime|1649796511|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Input File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010203004|XXGoport|62|0|160|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010501005|XXGpvertex|63|0|166|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Dedup_Sorted.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|keep|last|3|1|l|@{0|}}
{30001002|XXparameter|key|\{\}|3|2|$|@{0|}}
{30001002|XXparameter|dup_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Dedup Sorted|132000|321000|0|0|0|0|161|Dedup Sorted-1|Ab Initio Software|Built-in 2.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|64|0|168|0|{@{}@0|0|0|0|out|0.0|@@@2196|0|}}
{2010203004|XXGoport|65|0|171|0|{@{}@0|0|0|0|dup|0.0|@@@2192|0|}}
{2010203004|XXGoport|66|0|174|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|67|0|176|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|68|0|178|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|69|0|180|0|{@{}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|70|0|183|0|{Separates one specified data record in each group of data records from the rest of the records in the group.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|dedup|3|1|Hl||{0|}}
{30001002|XXparameter|image__|/~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|key||19|2|RFO$|Key on which to remove duplicates|{0|}}
{30001002|XXparameter|select||20|2|FK$|Optional select expression|{0|}}
{30001002|XXparameter|keep|first|15|1|FKl|Output record for a group of duplicates|{3|first|last|unique-only|}}
{30001002|XXparameter|package||8|1|FKl|Package containing transforms and data types|{0|}}
{30001002|XXparameter|package.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version :2.12.999.m999|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword2|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword2.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp ramp_keyword2 ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|check_sort|True|13|1|FKl|Abort on first record that is out of sorted order|{0|}}
{30001002|XXparameter|check_sort.display_name|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.keyword|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.condition|version 2.11.1:|3|15|P?|@{0|}}
{30001002|XXparameter|check_sort.update_clauses|update_value False|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|NoHidePorts|out|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|reject=in; out=in; dup=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select); dup=filter(select)|3|2|H$||{0|}}
{30001002|XXparameter|num_types|2|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation1|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation2|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation3|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|num_operations|4|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|num_callbacks|4|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|dup_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,dup,reject,error,log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1649796515|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: dup = in
metadata type: in = out
metadata type: in = dup|3|1|FHKl|@{0|}}
}}@0|Dedup Sorted|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|71|0|185|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2196|0|}}
{2010203004|XXGoport|72|0|188|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|dup|0.0|@@@2192|0|}}
{2010203004|XXGoport|73|0|191|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|74|0|194|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|75|0|197|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|76|0|200|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|77|0|210|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|out0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|select|V_CASE_NBR =='I2122310013'|3|2|$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|transform0|out :: reformat(in) =
begin
  out.V_NUM_REFADQUIRENTE :: 'ABC';
  out.D_FECHA_COMPRA :: '0001-01-01';
  out.N_IMP_TRNMONDESTINO :: 123;
  out.V_TYPE_REFOUND :: 'ABC';
  out.N_HIERARCHY :: 123;
  out.* :: in.*;
  out.MIS_DATE :: '2022-12-26';
end;|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Reformat|325000|350000|0|0|0|0|164|Reformat|Ab Initio Software|Built-in 1.0:|1|100|0||6||1|1|{1|0|}}}
{2010203004|XXGoport|78|0|212|0|{@{}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|79|0|215|0|{@{}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|80|0|217|0|{@{}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|81|0|219|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|82|0|221|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|83|0|224|0|{Changes the record format of your data by dropping fields or by using DML expressions to add fields, combine fields, or modify the data.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|reformat-transform|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|count|1|1|1|Fl|Number of reformat transforms|{0|}}
{30001002|XXparameter|count.is_index|true|3|9|P|@{0|}}
{30001002|XXparameter|transform0||8|1|FOl|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
{30001002|XXparameter|select||20|2|FK$|Filter expression before reformatting|{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version :2.12.999.m999|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword2|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword2.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp ramp_keyword2 ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|output_index||8|1|FKl|Output index computation|{0|}}
{30001002|XXparameter|output_index.display_name|output-index|3|9|P|@{0|}}
{30001002|XXparameter|output_index.keyword|output-index|3|9|P|@{0|}}
{30001002|XXparameter|output_index_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_index_port.display_name|output-index_port|3|9|P|@{0|}}
{30001002|XXparameter|output_index_port.keyword|output-index_port|3|9|P|@{0|}}
{30001002|XXparameter|output_index_signature|int output_index_out::output_index(in)|3|2|H$|Function returning index of output port|{0|}}
{30001002|XXparameter|output_index_signature.display_name|output-index_signature|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes||8|1|FKl|Output index vector computation|{0|}}
{30001002|XXparameter|output_indexes.display_name|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes.keyword|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_indexes_port.display_name|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port.keyword|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_signature|int[int] output_indexes_out::output_indexes(in)|3|2|H$|Function returning vector of indexes of output ports|{0|}}
{30001002|XXparameter|output_indexes_signature.display_name|output-indexes_signature|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|num_operations|7|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|out::reformat(in)|3|2|H$|Reformat operation|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out*|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|legacy_xfr;reject*=in;out*=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select)|3|2|H$||{0|}}
{30001002|XXparameter|num_types|3|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type3|event_info_t event_info "record int event_type; end"|3|2|H$|Information about the kind of event that happened|{0|}}
{30001002|XXparameter|operation2|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation3|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation6|optional out::output_at_event(event_info)|3|2|H$|Function to allow the output of an additional record at event|{0|}}
{30001002|XXparameter|operation7|optional ::on_startup(long in_recovery)|3|2|H$|Function executed at graph startup|{0|}}
{30001002|XXparameter|num_callbacks|6|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|main_mp_port|count out|3|1|l||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject0_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error0_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out[*],reject[*],error[*],log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1649796515|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Reformat|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|84|0|226|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform0||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|85|0|230|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|86|0|233|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|87|0|236|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|88|0|239|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010110002|XXGconstant|89|0|246|0|{@{}@{1|2457075|}}}
{2010002001|XXGdirectory_object_object|0|1|2|0|{XXGgraph|}0|1|}
{2010704001|XXGgraph_graphinfo_graphinfo|1|0|2|0|{}1|2|}
{2010706001|XXGgraphinfo_runsettings_runsettings|2|0|4|0|{}2|3|}
{2010109001|XXGobject_property_value|3|0|6|0|{0|legend_face|92|}2|4|}
{2010604001|XXGgraph_flow_flow|4|0|8|0|{Flow_1|}1|5|}
{2010604001|XXGgraph_flow_flow|5|0|10|0|{Flow_2|}1|6|}
{2010604001|XXGgraph_flow_flow|6|0|12|0|{Flow_3|}1|7|}
{2010604001|XXGgraph_flow_flow|7|0|14|0|{Flow_4|}1|8|}
{2010604001|XXGgraph_flow_flow|8|0|16|0|{Flow_5|}1|9|}
{2010604001|XXGgraph_flow_flow|9|0|18|0|{Flow_6|}1|10|}
{2010604001|XXGgraph_flow_flow|10|0|20|0|{Flow_7|}1|11|}
{2010601001|XXGgraph_vertex_vertex|11|0|22|0|{ADS_Table_Input|}1|12|}
{2010604001|XXGgraph_flow_flow|12|0|24|0|{Flow_8|}12|13|}
{2010604001|XXGgraph_flow_flow|13|0|26|0|{Flow_9|}12|14|}
{2010601001|XXGgraph_vertex_vertex|14|0|28|0|{Input_File_3|}12|15|}
{2010212001|XXGvertex_oport_oport|15|0|30|0|{0|read|}15|16|}
{2010213001|XXGoport_dst_flow|16|0|32|0|{0|}16|13|}
{2010007001|XXGobject_proto_object|17|0|33|0|{}15|17|}
{2010212001|XXGvertex_oport_oport|18|0|35|0|{0|read|}17|18|}
{2010006001|XXGobject_psameas_object|19|0|37|0|{metadata|read_metadata|1|0|}18|17|}
{2010601001|XXGgraph_vertex_vertex|20|0|38|0|{Input_File_4|}12|19|}
{2010211001|XXGvertex_iport_iport|21|0|40|0|{0|write|}19|20|}
{2010214001|XXGiport_src_flow|22|0|42|0|{0|}20|14|}
{2010007001|XXGobject_proto_object|23|0|43|0|{}19|21|}
{2010211001|XXGvertex_iport_iport|24|0|45|0|{0|write|}21|22|}
{2010006001|XXGobject_psameas_object|25|0|47|0|{metadata|write_metadata|1|0|}22|21|}
{2010601001|XXGgraph_vertex_vertex|26|0|48|0|{Reformat_1|}12|23|}
{2010212001|XXGvertex_oport_oport|27|0|50|0|{0|out0|}23|24|}
{2010213001|XXGoport_dst_flow|28|0|52|0|{0|}24|14|}
{2010212001|XXGvertex_oport_oport|29|0|53|0|{1|reject0|}23|25|}
{2010212001|XXGvertex_oport_oport|30|0|55|0|{2|error0|}23|26|}
{2010212001|XXGvertex_oport_oport|31|0|57|0|{3|log|}23|27|}
{2010211001|XXGvertex_iport_iport|32|0|59|0|{0|in|}23|28|}
{2010214001|XXGiport_src_flow|33|0|61|0|{0|}28|13|}
{2010007001|XXGobject_proto_object|34|0|62|0|{}23|29|}
{2010212001|XXGvertex_oport_oport|35|0|64|0|{0|out0|}29|30|}
{2010006001|XXGobject_psameas_object|36|0|66|0|{metadata|out0_metadata|1|0|}30|29|}
{2010006001|XXGobject_psameas_object|37|0|67|0|{transform0|transform0|1|0|}30|29|}
{2010212001|XXGvertex_oport_oport|38|0|68|0|{1|reject0|}29|31|}
{2010006001|XXGobject_psameas_object|39|0|70|0|{metadata|reject0_metadata|1|0|}31|29|}
{2010212001|XXGvertex_oport_oport|40|0|71|0|{2|error0|}29|32|}
{2010006001|XXGobject_psameas_object|41|0|73|0|{metadata|error0_metadata|1|0|}32|29|}
{2010212001|XXGvertex_oport_oport|42|0|74|0|{3|log|}29|33|}
{2010006001|XXGobject_psameas_object|43|0|76|0|{metadata|log_metadata|1|0|}33|29|}
{2010211001|XXGvertex_iport_iport|44|0|77|0|{0|in|}29|34|}
{2010006001|XXGobject_psameas_object|45|0|79|0|{metadata|in_metadata|1|0|}34|29|}
{2010006001|XXGobject_psameas_object|46|0|80|0|{Layout|Layout|0|0|}23|19|}
{2010006001|XXGobject_psameas_object|47|0|81|0|{in_metadata|read_metadata|0|0|}23|15|}
{2010006001|XXGobject_psameas_object|48|0|82|0|{out0_metadata|write_metadata|0|0|}23|19|}
{2010006001|XXGobject_psameas_object|49|0|83|0|{reject0_metadata|read_metadata|0|0|}23|15|}
{2010601001|XXGgraph_vertex_vertex|50|0|84|0|{Concatenate|}1|35|}
{2010212001|XXGvertex_oport_oport|51|0|86|0|{0|out|}35|36|}
{2010213001|XXGoport_dst_flow|52|0|88|0|{0|}36|11|}
{2010211001|XXGvertex_iport_iport|53|0|89|0|{0|in|}35|37|}
{2010214001|XXGiport_src_flow|54|0|91|0|{0|}37|6|}
{2010214001|XXGiport_src_flow|55|0|92|0|{1|}37|9|}
{2010214001|XXGiport_src_flow|56|0|93|0|{2|}37|10|}
{2010007001|XXGobject_proto_object|57|0|94|0|{}35|38|}
{2010212001|XXGvertex_oport_oport|58|0|96|0|{0|out|}38|39|}
{2010006001|XXGobject_psameas_object|59|0|98|0|{metadata|out_metadata|1|0|}39|38|}
{2010211001|XXGvertex_iport_iport|60|0|99|0|{0|in|}38|40|}
{2010006001|XXGobject_psameas_object|61|0|101|0|{metadata|in_metadata|1|0|}40|38|}
{2010006001|XXGobject_psameas_object|62|0|102|0|{Layout|Layout|0|0|}35|41|}
{2010211001|XXGvertex_iport_iport|63|0|104|0|{0|write|}41|42|}
{2010214001|XXGiport_src_flow|64|0|106|0|{0|}42|11|}
{2010007001|XXGobject_proto_object|65|0|107|0|{}41|43|}
{2010211001|XXGvertex_iport_iport|66|0|109|0|{0|write|}43|44|}
{2010006001|XXGobject_psameas_object|67|0|111|0|{metadata|write_metadata|1|0|}44|43|}
{2010006001|XXGobject_psameas_object|68|0|112|0|{in_metadata|write_metadata|0|0|}35|41|}
{2010006001|XXGobject_psameas_object|69|0|113|0|{out_metadata|write_metadata|0|0|}35|41|}
{2010601001|XXGgraph_vertex_vertex|70|0|114|0|{Dedup_Sorted|}1|45|}
{2010212001|XXGvertex_oport_oport|71|0|116|0|{0|out|}45|46|}
{2010213001|XXGoport_dst_flow|72|0|118|0|{0|}46|6|}
{2010212001|XXGvertex_oport_oport|73|0|119|0|{1|dup|}45|47|}
{2010213001|XXGoport_dst_flow|74|0|121|0|{0|}47|7|}
{2010212001|XXGvertex_oport_oport|75|0|122|0|{2|reject|}45|48|}
{2010212001|XXGvertex_oport_oport|76|0|124|0|{3|error|}45|49|}
{2010212001|XXGvertex_oport_oport|77|0|126|0|{4|log|}45|50|}
{2010211001|XXGvertex_iport_iport|78|0|128|0|{0|in|}45|51|}
{2010214001|XXGiport_src_flow|79|0|130|0|{0|}51|5|}
{2010007001|XXGobject_proto_object|80|0|131|0|{}45|52|}
{2010212001|XXGvertex_oport_oport|81|0|133|0|{0|out|}52|53|}
{2010006001|XXGobject_psameas_object|82|0|135|0|{metadata|out_metadata|1|0|}53|52|}
{2010212001|XXGvertex_oport_oport|83|0|136|0|{1|dup|}52|54|}
{2010006001|XXGobject_psameas_object|84|0|138|0|{metadata|dup_metadata|1|0|}54|52|}
{2010212001|XXGvertex_oport_oport|85|0|139|0|{2|reject|}52|55|}
{2010006001|XXGobject_psameas_object|86|0|141|0|{metadata|reject_metadata|1|0|}55|52|}
{2010212001|XXGvertex_oport_oport|87|0|142|0|{3|error|}52|56|}
{2010006001|XXGobject_psameas_object|88|0|144|0|{metadata|error_metadata|1|0|}56|52|}
{2010212001|XXGvertex_oport_oport|89|0|145|0|{4|log|}52|57|}
{2010006001|XXGobject_psameas_object|90|0|147|0|{metadata|log_metadata|1|0|}57|52|}
{2010211001|XXGvertex_iport_iport|91|0|148|0|{0|in|}52|58|}
{2010006001|XXGobject_psameas_object|92|0|150|0|{metadata|in_metadata|1|0|}58|52|}
{2010006001|XXGobject_psameas_object|93|0|151|0|{Layout|Layout|0|0|}45|41|}
{2010006001|XXGobject_psameas_object|94|0|152|0|{dup_metadata|read_metadata|0|0|}45|59|}
{2010212001|XXGvertex_oport_oport|95|0|154|0|{0|read|}59|60|}
{2010213001|XXGoport_dst_flow|96|0|156|0|{0|}60|5|}
{2010007001|XXGobject_proto_object|97|0|157|0|{}59|61|}
{2010212001|XXGvertex_oport_oport|98|0|159|0|{0|read|}61|62|}
{2010006001|XXGobject_psameas_object|99|0|161|0|{metadata|read_metadata|1|0|}62|61|}
{2010006001|XXGobject_psameas_object|100|0|162|0|{in_metadata|read_metadata|0|0|}45|59|}
{2010006001|XXGobject_psameas_object|101|0|163|0|{out_metadata|read_metadata|0|0|}45|59|}
{2010006001|XXGobject_psameas_object|102|0|164|0|{reject_metadata|read_metadata|0|0|}45|59|}
{2010601001|XXGgraph_vertex_vertex|103|0|165|0|{Dedup_Sorted_1|}1|63|}
{2010212001|XXGvertex_oport_oport|104|0|167|0|{0|out|}63|64|}
{2010213001|XXGoport_dst_flow|105|0|169|0|{0|}64|10|}
{2010212001|XXGvertex_oport_oport|106|0|170|0|{1|dup|}63|65|}
{2010213001|XXGoport_dst_flow|107|0|172|0|{0|}65|8|}
{2010212001|XXGvertex_oport_oport|108|0|173|0|{2|reject|}63|66|}
{2010212001|XXGvertex_oport_oport|109|0|175|0|{3|error|}63|67|}
{2010212001|XXGvertex_oport_oport|110|0|177|0|{4|log|}63|68|}
{2010211001|XXGvertex_iport_iport|111|0|179|0|{0|in|}63|69|}
{2010214001|XXGiport_src_flow|112|0|181|0|{0|}69|7|}
{2010007001|XXGobject_proto_object|113|0|182|0|{}63|70|}
{2010212001|XXGvertex_oport_oport|114|0|184|0|{0|out|}70|71|}
{2010006001|XXGobject_psameas_object|115|0|186|0|{metadata|out_metadata|1|0|}71|70|}
{2010212001|XXGvertex_oport_oport|116|0|187|0|{1|dup|}70|72|}
{2010006001|XXGobject_psameas_object|117|0|189|0|{metadata|dup_metadata|1|0|}72|70|}
{2010212001|XXGvertex_oport_oport|118|0|190|0|{2|reject|}70|73|}
{2010006001|XXGobject_psameas_object|119|0|192|0|{metadata|reject_metadata|1|0|}73|70|}
{2010212001|XXGvertex_oport_oport|120|0|193|0|{3|error|}70|74|}
{2010006001|XXGobject_psameas_object|121|0|195|0|{metadata|error_metadata|1|0|}74|70|}
{2010212001|XXGvertex_oport_oport|122|0|196|0|{4|log|}70|75|}
{2010006001|XXGobject_psameas_object|123|0|198|0|{metadata|log_metadata|1|0|}75|70|}
{2010211001|XXGvertex_iport_iport|124|0|199|0|{0|in|}70|76|}
{2010006001|XXGobject_psameas_object|125|0|201|0|{metadata|in_metadata|1|0|}76|70|}
{2010006001|XXGobject_psameas_object|126|0|202|0|{Layout|Layout|0|0|}63|41|}
{2010006001|XXGobject_psameas_object|127|0|203|0|{dup_metadata|read_metadata|0|0|}63|59|}
{2010006001|XXGobject_psameas_object|128|0|204|0|{in_metadata|read_metadata|0|0|}63|59|}
{2010006001|XXGobject_psameas_object|129|0|205|0|{out_metadata|read_metadata|0|0|}63|59|}
{2010006001|XXGobject_psameas_object|130|0|206|0|{reject_metadata|read_metadata|0|0|}63|59|}
{2010601001|XXGgraph_vertex_vertex|131|0|207|0|{Input_File_1|}1|59|}
{2010601001|XXGgraph_vertex_vertex|132|0|208|0|{Input_File_2|}1|41|}
{2010601001|XXGgraph_vertex_vertex|133|0|209|0|{Reformat|}1|77|}
{2010212001|XXGvertex_oport_oport|134|0|211|0|{0|out0|}77|78|}
{2010213001|XXGoport_dst_flow|135|0|213|0|{0|}78|9|}
{2010212001|XXGvertex_oport_oport|136|0|214|0|{1|reject0|}77|79|}
{2010212001|XXGvertex_oport_oport|137|0|216|0|{2|error0|}77|80|}
{2010212001|XXGvertex_oport_oport|138|0|218|0|{3|log|}77|81|}
{2010211001|XXGvertex_iport_iport|139|0|220|0|{0|in|}77|82|}
{2010214001|XXGiport_src_flow|140|0|222|0|{0|}82|8|}
{2010007001|XXGobject_proto_object|141|0|223|0|{}77|83|}
{2010212001|XXGvertex_oport_oport|142|0|225|0|{0|out0|}83|84|}
{2010006001|XXGobject_psameas_object|143|0|227|0|{metadata|out0_metadata|1|0|}84|83|}
{2010006001|XXGobject_psameas_object|144|0|228|0|{transform0|transform0|1|0|}84|83|}
{2010212001|XXGvertex_oport_oport|145|0|229|0|{1|reject0|}83|85|}
{2010006001|XXGobject_psameas_object|146|0|231|0|{metadata|reject0_metadata|1|0|}85|83|}
{2010212001|XXGvertex_oport_oport|147|0|232|0|{2|error0|}83|86|}
{2010006001|XXGobject_psameas_object|148|0|234|0|{metadata|error0_metadata|1|0|}86|83|}
{2010212001|XXGvertex_oport_oport|149|0|235|0|{3|log|}83|87|}
{2010006001|XXGobject_psameas_object|150|0|237|0|{metadata|log_metadata|1|0|}87|83|}
{2010211001|XXGvertex_iport_iport|151|0|238|0|{0|in|}83|88|}
{2010006001|XXGobject_psameas_object|152|0|240|0|{metadata|in_metadata|1|0|}88|83|}
{2010006001|XXGobject_psameas_object|153|0|241|0|{Layout|Layout|0|0|}77|41|}
{2010006001|XXGobject_psameas_object|154|0|242|0|{in_metadata|read_metadata|0|0|}77|59|}
{2010006001|XXGobject_psameas_object|155|0|243|0|{out0_metadata|write_metadata|0|0|}77|41|}
{2010006001|XXGobject_psameas_object|156|0|244|0|{reject0_metadata|read_metadata|0|0|}77|59|}
{2010109001|XXGobject_property_value|157|0|245|0|{0|TrackingThumbprint|72|}1|89|}

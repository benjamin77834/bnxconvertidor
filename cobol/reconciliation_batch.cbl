       IDENTIFICATION DIVISION.
       PROGRAM-ID. NIGHTLY-RECONCILIATION.
       AUTHOR. BNX-MIGRATION.
      * ============================================================
      * PROCESO NOCTURNO DE CONCILIACION BANCARIA
      * Concilia movimientos del core vs switches de pago,
      * detecta diferencias, calcula comisiones, genera reportes
      * regulatorios y operativos.
      * ============================================================

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CORE-MOVEMENTS ASSIGN TO 'COREMOV'
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-CORE-STATUS.
           SELECT SWITCH-MOVEMENTS ASSIGN TO 'SWITCHMOV'
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-SWITCH-STATUS.
           SELECT CUSTOMER-MASTER ASSIGN TO 'CUSTMST'
               ORGANIZATION IS SEQUENTIAL.
           SELECT ACCOUNT-MASTER ASSIGN TO 'ACCTMST'
               ORGANIZATION IS SEQUENTIAL.
           SELECT PRODUCT-CATALOG ASSIGN TO 'PRODCAT'
               ORGANIZATION IS SEQUENTIAL.
           SELECT COMMISSION-TABLE ASSIGN TO 'COMMTBL'
               ORGANIZATION IS SEQUENTIAL.
           SELECT EXCHANGE-RATES ASSIGN TO 'FXRATES'
               ORGANIZATION IS SEQUENTIAL.
           SELECT BRANCH-TABLE ASSIGN TO 'BRANCHTBL'
               ORGANIZATION IS SEQUENTIAL.
           SELECT RECONCILED-FILE ASSIGN TO 'RECONOUT'
               ORGANIZATION IS SEQUENTIAL.
           SELECT DIFFERENCE-REPORT ASSIGN TO 'DIFFRPT'
               ORGANIZATION IS SEQUENTIAL.
           SELECT COMMISSION-REPORT ASSIGN TO 'COMMRPT'
               ORGANIZATION IS SEQUENTIAL.
           SELECT REGULATORY-REPORT ASSIGN TO 'REGRPT'
               ORGANIZATION IS SEQUENTIAL.
           SELECT SUMMARY-REPORT ASSIGN TO 'SUMRPT'
               ORGANIZATION IS SEQUENTIAL.
           SELECT ERROR-FILE ASSIGN TO 'ERRFILE'
               ORGANIZATION IS SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD CORE-MOVEMENTS
           RECORDING MODE IS F
           RECORD CONTAINS 250 CHARACTERS.
       01 CORE-RECORD.
           05 CORE-TX-ID         PIC X(15).
           05 CORE-ACCOUNT       PIC X(18).
           05 CORE-CUSTOMER-ID   PIC X(10).
           05 CORE-AMOUNT        PIC S9(13)V99 COMP-3.
           05 CORE-CURRENCY      PIC X(3).
           05 CORE-TX-TYPE       PIC X(3).
           05 CORE-TX-DATE       PIC 9(8) COMP-3.
           05 CORE-TX-TIME       PIC 9(6) COMP-3.
           05 CORE-BRANCH        PIC X(4).
           05 CORE-CHANNEL       PIC X(3).
           05 CORE-PRODUCT       PIC X(6).
           05 CORE-REFERENCE     PIC X(20).
           05 CORE-STATUS        PIC X(1).
           05 CORE-AUTH-CODE     PIC X(6).
           05 FILLER             PIC X(148).

       FD SWITCH-MOVEMENTS
           RECORDING MODE IS F
           RECORD CONTAINS 200 CHARACTERS.
       01 SWITCH-RECORD.
           05 SW-TX-ID           PIC X(15).
           05 SW-CARD-NUMBER     PIC X(16).
           05 SW-MERCHANT-ID     PIC X(10).
           05 SW-AMOUNT          PIC S9(13)V99 COMP-3.
           05 SW-CURRENCY        PIC X(3).
           05 SW-TX-TYPE         PIC X(3).
           05 SW-TX-DATE         PIC 9(8) COMP-3.
           05 SW-TX-TIME         PIC 9(6) COMP-3.
           05 SW-AUTH-CODE       PIC X(6).
           05 SW-RESPONSE-CODE   PIC X(2).
           05 SW-NETWORK         PIC X(4).
           05 SW-COUNTRY         PIC X(3).
           05 FILLER             PIC X(121).

       FD CUSTOMER-MASTER.
       01 CUST-RECORD.
           05 CUST-ID            PIC X(10).
           05 CUST-NAME          PIC X(40).
           05 CUST-RFC           PIC X(13).
           05 CUST-SEGMENT       PIC X(10).
           05 CUST-RISK-LEVEL    PIC X(1).
           05 CUST-BRANCH        PIC X(4).
           05 CUST-SINCE-DATE    PIC 9(8) COMP-3.

       FD ACCOUNT-MASTER.
       01 ACCT-RECORD.
           05 ACCT-NUMBER        PIC X(18).
           05 ACCT-CUSTOMER-ID   PIC X(10).
           05 ACCT-TYPE          PIC X(3).
           05 ACCT-PRODUCT       PIC X(6).
           05 ACCT-BALANCE       PIC S9(13)V99 COMP-3.
           05 ACCT-AVAILABLE     PIC S9(13)V99 COMP-3.
           05 ACCT-CURRENCY      PIC X(3).
           05 ACCT-STATUS        PIC X(1).
           05 ACCT-OPEN-DATE     PIC 9(8) COMP-3.

       FD PRODUCT-CATALOG.
       01 PROD-RECORD.
           05 PROD-CODE          PIC X(6).
           05 PROD-NAME          PIC X(30).
           05 PROD-TYPE          PIC X(3).
           05 PROD-COMMISSION    PIC 9(3)V99 COMP-3.
           05 PROD-TAX-RATE      PIC 9(3)V99 COMP-3.

       FD COMMISSION-TABLE.
       01 COMM-RECORD.
           05 COMM-TX-TYPE       PIC X(3).
           05 COMM-CHANNEL       PIC X(3).
           05 COMM-RATE          PIC 9(3)V9(4) COMP-3.
           05 COMM-MIN           PIC S9(7)V99 COMP-3.
           05 COMM-MAX           PIC S9(7)V99 COMP-3.

       FD EXCHANGE-RATES.
       01 FX-RECORD.
           05 FX-CURRENCY        PIC X(3).
           05 FX-RATE-BUY        PIC 9(5)V9(6) COMP-3.
           05 FX-RATE-SELL       PIC 9(5)V9(6) COMP-3.
           05 FX-DATE            PIC 9(8) COMP-3.

       FD BRANCH-TABLE.
       01 BRANCH-RECORD.
           05 BRANCH-CODE        PIC X(4).
           05 BRANCH-NAME        PIC X(30).
           05 BRANCH-REGION      PIC X(10).
           05 BRANCH-CITY        PIC X(20).
           05 BRANCH-MANAGER     PIC X(10).

       FD RECONCILED-FILE.
       01 RECON-RECORD           PIC X(400).

       FD DIFFERENCE-REPORT.
       01 DIFF-RECORD            PIC X(400).

       FD COMMISSION-REPORT.
       01 COMM-RPT-RECORD        PIC X(400).

       FD REGULATORY-REPORT.
       01 REG-RECORD             PIC X(400).

       FD SUMMARY-REPORT.
       01 SUM-RECORD             PIC X(400).

       FD ERROR-FILE.
       01 ERR-RECORD             PIC X(400).

       WORKING-STORAGE SECTION.
       01 WS-CORE-STATUS         PIC XX VALUE SPACES.
       01 WS-SWITCH-STATUS       PIC XX VALUE SPACES.
       01 WS-MATCHED-COUNT       PIC 9(8) COMP VALUE 0.
       01 WS-UNMATCHED-CORE      PIC 9(8) COMP VALUE 0.
       01 WS-UNMATCHED-SWITCH    PIC 9(8) COMP VALUE 0.
       01 WS-DIFF-AMOUNT         PIC S9(15)V99 COMP-3 VALUE 0.
       01 WS-TOTAL-COMMISSION    PIC S9(13)V99 COMP-3 VALUE 0.
       01 WS-TOTAL-TAX           PIC S9(13)V99 COMP-3 VALUE 0.
       01 WS-AMOUNT-MXN          PIC S9(13)V99 COMP-3 VALUE 0.
       01 WS-COMMISSION-AMT      PIC S9(13)V99 COMP-3 VALUE 0.
       01 WS-ERROR-COUNT         PIC 9(8) COMP VALUE 0.
       01 WS-PROCESS-DATE        PIC 9(8) VALUE 0.

       PROCEDURE DIVISION.
       MAIN-PROCESS.
           OPEN INPUT CORE-MOVEMENTS
                      SWITCH-MOVEMENTS
                      CUSTOMER-MASTER
                      ACCOUNT-MASTER
                      PRODUCT-CATALOG
                      COMMISSION-TABLE
                      EXCHANGE-RATES
                      BRANCH-TABLE
           OPEN OUTPUT RECONCILED-FILE
                       DIFFERENCE-REPORT
                       COMMISSION-REPORT
                       REGULATORY-REPORT
                       SUMMARY-REPORT
                       ERROR-FILE

           PERFORM READ-ALL-INPUTS
           PERFORM FILTER-ACTIVE-ACCOUNTS
           PERFORM FILTER-SETTLED-CORE
           PERFORM FILTER-APPROVED-SWITCH
           PERFORM JOIN-CORE-WITH-ACCOUNT
           PERFORM JOIN-CORE-WITH-CUSTOMER
           PERFORM JOIN-CORE-WITH-PRODUCT
           PERFORM JOIN-CORE-WITH-BRANCH
           PERFORM JOIN-SWITCH-WITH-FX
           PERFORM MATCH-CORE-VS-SWITCH
           PERFORM COMPUTE-DIFFERENCES
           PERFORM COMPUTE-COMMISSION
           PERFORM COMPUTE-TAX
           PERFORM COMPUTE-MXN-AMOUNT
           PERFORM DETECT-UNMATCHED-CORE
           PERFORM DETECT-UNMATCHED-SWITCH
           PERFORM DETECT-AMOUNT-MISMATCH
           PERFORM DETECT-LARGE-DIFFERENCE
           PERFORM DETECT-SUSPICIOUS-PATTERN
           PERFORM WRITE-RECONCILED
           PERFORM WRITE-DIFFERENCES
           PERFORM WRITE-COMMISSIONS
           PERFORM WRITE-REGULATORY
           PERFORM WRITE-SUMMARY
           PERFORM WRITE-ERRORS

           CLOSE CORE-MOVEMENTS
                 SWITCH-MOVEMENTS
                 CUSTOMER-MASTER
                 ACCOUNT-MASTER
                 PRODUCT-CATALOG
                 COMMISSION-TABLE
                 EXCHANGE-RATES
                 BRANCH-TABLE
                 RECONCILED-FILE
                 DIFFERENCE-REPORT
                 COMMISSION-REPORT
                 REGULATORY-REPORT
                 SUMMARY-REPORT
                 ERROR-FILE
           STOP RUN.

       READ-ALL-INPUTS.
           READ CORE-MOVEMENTS INTO CORE-RECORD.
           READ SWITCH-MOVEMENTS INTO SWITCH-RECORD.
           READ CUSTOMER-MASTER INTO CUST-RECORD.
           READ ACCOUNT-MASTER INTO ACCT-RECORD.
           READ PRODUCT-CATALOG INTO PROD-RECORD.
           READ COMMISSION-TABLE INTO COMM-RECORD.
           READ EXCHANGE-RATES INTO FX-RECORD.
           READ BRANCH-TABLE INTO BRANCH-RECORD.

       FILTER-ACTIVE-ACCOUNTS.
           IF ACCT-STATUS = 'A'
               CONTINUE
           ELSE
               MOVE SPACES TO ACCT-RECORD
           END-IF.

       FILTER-SETTLED-CORE.
           IF CORE-STATUS = 'S' AND CORE-AMOUNT NOT = 0
               CONTINUE
           ELSE
               ADD 1 TO WS-ERROR-COUNT
               WRITE ERR-RECORD FROM CORE-RECORD
           END-IF.

       FILTER-APPROVED-SWITCH.
           IF SW-RESPONSE-CODE = '00' AND SW-AMOUNT NOT = 0
               CONTINUE
           ELSE
               ADD 1 TO WS-ERROR-COUNT
               WRITE ERR-RECORD FROM SWITCH-RECORD
           END-IF.

       JOIN-CORE-WITH-ACCOUNT.
           IF CORE-ACCOUNT = ACCT-NUMBER
               CONTINUE
           END-IF.

       JOIN-CORE-WITH-CUSTOMER.
           IF CORE-CUSTOMER-ID = CUST-ID
               CONTINUE
           END-IF.

       JOIN-CORE-WITH-PRODUCT.
           IF CORE-PRODUCT = PROD-CODE
               CONTINUE
           END-IF.

       JOIN-CORE-WITH-BRANCH.
           IF CORE-BRANCH = BRANCH-CODE
               CONTINUE
           END-IF.

       JOIN-SWITCH-WITH-FX.
           IF SW-CURRENCY = FX-CURRENCY
               CONTINUE
           END-IF.

       MATCH-CORE-VS-SWITCH.
           IF CORE-TX-ID = SW-TX-ID
               ADD 1 TO WS-MATCHED-COUNT
           END-IF.

       COMPUTE-DIFFERENCES.
           COMPUTE WS-DIFF-AMOUNT =
               CORE-AMOUNT - SW-AMOUNT.

       COMPUTE-COMMISSION.
           COMPUTE WS-COMMISSION-AMT =
               CORE-AMOUNT * COMM-RATE.
           IF WS-COMMISSION-AMT < COMM-MIN
               MOVE COMM-MIN TO WS-COMMISSION-AMT
           END-IF.
           IF WS-COMMISSION-AMT > COMM-MAX
               MOVE COMM-MAX TO WS-COMMISSION-AMT
           END-IF.
           ADD WS-COMMISSION-AMT TO WS-TOTAL-COMMISSION.

       COMPUTE-TAX.
           COMPUTE WS-TOTAL-TAX =
               WS-COMMISSION-AMT * PROD-TAX-RATE / 100.

       COMPUTE-MXN-AMOUNT.
           IF CORE-CURRENCY NOT = 'MXN'
               COMPUTE WS-AMOUNT-MXN =
                   CORE-AMOUNT * FX-RATE-SELL
           ELSE
               MOVE CORE-AMOUNT TO WS-AMOUNT-MXN
           END-IF.

       DETECT-UNMATCHED-CORE.
           IF CORE-TX-ID NOT = SW-TX-ID
               ADD 1 TO WS-UNMATCHED-CORE
               WRITE DIFF-RECORD FROM CORE-RECORD
           END-IF.

       DETECT-UNMATCHED-SWITCH.
           IF SW-TX-ID NOT = CORE-TX-ID
               ADD 1 TO WS-UNMATCHED-SWITCH
               WRITE DIFF-RECORD FROM SWITCH-RECORD
           END-IF.

       DETECT-AMOUNT-MISMATCH.
           IF WS-DIFF-AMOUNT NOT = 0
               WRITE DIFF-RECORD FROM CORE-RECORD
           END-IF.

       DETECT-LARGE-DIFFERENCE.
           IF WS-DIFF-AMOUNT > 10000
              OR WS-DIFF-AMOUNT < -10000
               WRITE REG-RECORD FROM CORE-RECORD
           END-IF.

       DETECT-SUSPICIOUS-PATTERN.
           IF WS-AMOUNT-MXN > 50000
              AND CUST-RISK-LEVEL = 'H'
               WRITE REG-RECORD FROM CORE-RECORD
           END-IF.

       WRITE-RECONCILED.
           WRITE RECON-RECORD FROM CORE-RECORD
           ADD 1 TO WS-MATCHED-COUNT.

       WRITE-DIFFERENCES.
           WRITE DIFF-RECORD FROM CORE-RECORD.

       WRITE-COMMISSIONS.
           WRITE COMM-RPT-RECORD FROM CORE-RECORD.

       WRITE-REGULATORY.
           WRITE REG-RECORD FROM CORE-RECORD.

       WRITE-SUMMARY.
           WRITE SUM-RECORD FROM CORE-RECORD.

       WRITE-ERRORS.
           WRITE ERR-RECORD FROM CORE-RECORD.

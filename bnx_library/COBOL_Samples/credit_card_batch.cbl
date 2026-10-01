       IDENTIFICATION DIVISION.
       PROGRAM-ID. CREDIT-CARD-BATCH.
       AUTHOR. BNX-MIGRATION.
      * ============================================================
      * PROCESO BATCH DIARIO DE TARJETAS DE CREDITO
      * Lee transacciones, clientes, cuentas y limites.
      * Calcula saldos, detecta fraude, genera reportes.
      * ============================================================

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT TRANSACTION-FILE ASSIGN TO 'TXFILE'
               ORGANIZATION IS SEQUENTIAL.
           SELECT CUSTOMER-FILE ASSIGN TO 'CUSTFILE'
               ORGANIZATION IS SEQUENTIAL.
           SELECT ACCOUNT-FILE ASSIGN TO 'ACCTFILE'
               ORGANIZATION IS SEQUENTIAL.
           SELECT CARD-FILE ASSIGN TO 'CARDFILE'
               ORGANIZATION IS SEQUENTIAL.
           SELECT MERCHANT-FILE ASSIGN TO 'MERCHFILE'
               ORGANIZATION IS SEQUENTIAL.
           SELECT LIMIT-FILE ASSIGN TO 'LIMITFILE'
               ORGANIZATION IS SEQUENTIAL.
           SELECT BALANCE-REPORT ASSIGN TO 'BALRPT'
               ORGANIZATION IS SEQUENTIAL.
           SELECT FRAUD-REPORT ASSIGN TO 'FRAUDRPT'
               ORGANIZATION IS SEQUENTIAL.
           SELECT STATEMENT-FILE ASSIGN TO 'STMTFILE'
               ORGANIZATION IS SEQUENTIAL.
           SELECT REJECT-FILE ASSIGN TO 'REJFILE'
               ORGANIZATION IS SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD TRANSACTION-FILE.
       01 TRANSACTION-RECORD.
           05 TX-ID              PIC X(15).
           05 TX-CARD-ID         PIC X(16).
           05 TX-MERCHANT-ID     PIC X(10).
           05 TX-AMOUNT          PIC S9(10)V99.
           05 TX-CURRENCY        PIC X(3).
           05 TX-TYPE            PIC X(3).
           05 TX-DATE            PIC X(10).
           05 TX-TIME            PIC X(8).
           05 TX-STATUS          PIC X(1).
           05 TX-AUTH-CODE       PIC X(6).
           05 TX-COUNTRY         PIC X(3).

       FD CUSTOMER-FILE.
       01 CUSTOMER-RECORD.
           05 CUST-ID            PIC X(10).
           05 CUST-NAME          PIC X(40).
           05 CUST-EMAIL         PIC X(50).
           05 CUST-PHONE         PIC X(15).
           05 CUST-SEGMENT       PIC X(10).
           05 CUST-RISK-LEVEL    PIC X(1).
           05 CUST-SINCE-DATE    PIC X(10).

       FD ACCOUNT-FILE.
       01 ACCOUNT-RECORD.
           05 ACCT-ID            PIC X(12).
           05 ACCT-CUST-ID       PIC X(10).
           05 ACCT-TYPE          PIC X(3).
           05 ACCT-BALANCE       PIC S9(12)V99.
           05 ACCT-CREDIT-LIMIT  PIC 9(10)V99.
           05 ACCT-STATUS        PIC X(1).
           05 ACCT-OPEN-DATE     PIC X(10).

       FD CARD-FILE.
       01 CARD-RECORD.
           05 CARD-ID            PIC X(16).
           05 CARD-ACCT-ID       PIC X(12).
           05 CARD-CUST-ID       PIC X(10).
           05 CARD-TYPE          PIC X(10).
           05 CARD-EXPIRY        PIC X(7).
           05 CARD-STATUS        PIC X(1).
           05 CARD-DAILY-LIMIT   PIC 9(8)V99.

       FD MERCHANT-FILE.
       01 MERCHANT-RECORD.
           05 MERCH-ID           PIC X(10).
           05 MERCH-NAME         PIC X(40).
           05 MERCH-CATEGORY     PIC X(10).
           05 MERCH-COUNTRY      PIC X(3).
           05 MERCH-RISK-SCORE   PIC 9V99.

       FD LIMIT-FILE.
       01 LIMIT-RECORD.
           05 LIMIT-CARD-TYPE    PIC X(10).
           05 LIMIT-DAILY-MAX    PIC 9(8)V99.
           05 LIMIT-MONTHLY-MAX  PIC 9(10)V99.
           05 LIMIT-SINGLE-MAX   PIC 9(8)V99.

       FD BALANCE-REPORT.
       01 BALANCE-RECORD         PIC X(300).

       FD FRAUD-REPORT.
       01 FRAUD-RECORD           PIC X(300).

       FD STATEMENT-FILE.
       01 STATEMENT-RECORD       PIC X(300).

       FD REJECT-FILE.
       01 REJECT-RECORD          PIC X(300).

       WORKING-STORAGE SECTION.
       01 WS-DAILY-TOTAL         PIC S9(12)V99 VALUE 0.
       01 WS-FRAUD-COUNT         PIC 9(8) VALUE 0.
       01 WS-REJECT-COUNT        PIC 9(8) VALUE 0.
       01 WS-TX-COUNT            PIC 9(8) VALUE 0.
       01 WS-AVAILABLE-CREDIT    PIC S9(12)V99 VALUE 0.
       01 WS-OVER-LIMIT-FLAG     PIC X VALUE 'N'.
       01 WS-FRAUD-FLAG          PIC X VALUE 'N'.

       PROCEDURE DIVISION.
       MAIN-PROCESS.
           OPEN INPUT TRANSACTION-FILE
                      CUSTOMER-FILE
                      ACCOUNT-FILE
                      CARD-FILE
                      MERCHANT-FILE
                      LIMIT-FILE
           OPEN OUTPUT BALANCE-REPORT
                       FRAUD-REPORT
                       STATEMENT-FILE
                       REJECT-FILE

           PERFORM READ-ALL-FILES
           PERFORM FILTER-ACTIVE-CARDS
           PERFORM FILTER-APPROVED-TX
           PERFORM FILTER-ACTIVE-ACCOUNTS
           PERFORM JOIN-TX-WITH-CARD
           PERFORM JOIN-TX-WITH-MERCHANT
           PERFORM JOIN-TX-WITH-ACCOUNT
           PERFORM JOIN-CARD-WITH-LIMITS
           PERFORM COMPUTE-DAILY-TOTALS
           PERFORM COMPUTE-AVAILABLE-CREDIT
           PERFORM DETECT-OVER-LIMIT
           PERFORM DETECT-FRAUD
           PERFORM DETECT-HIGH-RISK-MERCHANT
           PERFORM WRITE-BALANCE-REPORT
           PERFORM WRITE-FRAUD-REPORT
           PERFORM WRITE-STATEMENTS
           PERFORM WRITE-REJECTS

           CLOSE TRANSACTION-FILE
                 CUSTOMER-FILE
                 ACCOUNT-FILE
                 CARD-FILE
                 MERCHANT-FILE
                 LIMIT-FILE
                 BALANCE-REPORT
                 FRAUD-REPORT
                 STATEMENT-FILE
                 REJECT-FILE
           STOP RUN.

       READ-ALL-FILES.
           READ TRANSACTION-FILE INTO TRANSACTION-RECORD.
           READ CUSTOMER-FILE INTO CUSTOMER-RECORD.
           READ ACCOUNT-FILE INTO ACCOUNT-RECORD.
           READ CARD-FILE INTO CARD-RECORD.
           READ MERCHANT-FILE INTO MERCHANT-RECORD.
           READ LIMIT-FILE INTO LIMIT-RECORD.

       FILTER-ACTIVE-CARDS.
           IF CARD-STATUS = 'A' AND CARD-EXPIRY > '2026-01'
               CONTINUE
           ELSE
               MOVE SPACES TO CARD-RECORD
           END-IF.

       FILTER-APPROVED-TX.
           IF TX-STATUS = 'A' AND TX-AMOUNT > 0
               CONTINUE
           ELSE
               ADD 1 TO WS-REJECT-COUNT
               WRITE REJECT-RECORD FROM TRANSACTION-RECORD
           END-IF.

       FILTER-ACTIVE-ACCOUNTS.
           IF ACCT-STATUS = 'A'
               CONTINUE
           ELSE
               MOVE SPACES TO ACCOUNT-RECORD
           END-IF.

       JOIN-TX-WITH-CARD.
           IF TX-CARD-ID = CARD-ID
               CONTINUE
           END-IF.

       JOIN-TX-WITH-MERCHANT.
           IF TX-MERCHANT-ID = MERCH-ID
               CONTINUE
           END-IF.

       JOIN-TX-WITH-ACCOUNT.
           IF CARD-ACCT-ID = ACCT-ID
               CONTINUE
           END-IF.

       JOIN-CARD-WITH-LIMITS.
           IF CARD-TYPE = LIMIT-CARD-TYPE
               CONTINUE
           END-IF.

       COMPUTE-DAILY-TOTALS.
           ADD TX-AMOUNT TO WS-DAILY-TOTAL
           ADD 1 TO WS-TX-COUNT.

       COMPUTE-AVAILABLE-CREDIT.
           COMPUTE WS-AVAILABLE-CREDIT =
               ACCT-CREDIT-LIMIT - ACCT-BALANCE - TX-AMOUNT.

       DETECT-OVER-LIMIT.
           IF WS-AVAILABLE-CREDIT < 0
               MOVE 'Y' TO WS-OVER-LIMIT-FLAG
           END-IF.

       DETECT-FRAUD.
           IF TX-AMOUNT > LIMIT-SINGLE-MAX
              OR TX-COUNTRY NOT = MERCH-COUNTRY
               MOVE 'Y' TO WS-FRAUD-FLAG
               ADD 1 TO WS-FRAUD-COUNT
           END-IF.

       DETECT-HIGH-RISK-MERCHANT.
           IF MERCH-RISK-SCORE > 0.80
               MOVE 'Y' TO WS-FRAUD-FLAG
           END-IF.

       WRITE-BALANCE-REPORT.
           WRITE BALANCE-RECORD FROM ACCOUNT-RECORD.

       WRITE-FRAUD-REPORT.
           WRITE FRAUD-RECORD FROM TRANSACTION-RECORD.

       WRITE-STATEMENTS.
           WRITE STATEMENT-RECORD FROM TRANSACTION-RECORD.

       WRITE-REJECTS.
           WRITE REJECT-RECORD FROM TRANSACTION-RECORD.

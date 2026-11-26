import neural.studio.*;
import java.time.LocalTime;

import java.time.format.DateTimeFormatter;

import java.util.Random;



/**

 * Standardized Ledger Data Record.

 * Internal model mapping verified personal transaction values.

 */

class TransactionModel {

    private final String timestamp;

    private final String emailNode;

    private final String accountNum;

    private final String sortCode;

    private final String merchant;

    private final double valueGbp;

    private final String auditStatus;



    public TransactionModel(String email, String acc, String sort, String merchant, double value, String status) {

        this.timestamp = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));

        this.emailNode = email;

        this.accountNum = acc;

        this.sortCode = sort;

        this.merchant = merchant;

        this.valueGbp = value;

        this.auditStatus = status;

    }



    public void printRecord() {

        System.out.printf("      ├── [LEDGER_COMMIT] Time: %s | Op: %-12s | Amount: £%-7.2f | Status: %s\n",

                timestamp, merchant, valueGbp, auditStatus);

    }

}




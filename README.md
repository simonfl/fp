# Financial planning

A Monte Carlo simulation of your financial future

Define your model in main.py. This determines your income, expenses, saving, investments, mortgage, retirement date, and in general the rules for how money flows between your accounts. Then it runs your model each month over the next however many years, keeping track of each deposit, transfer and withdrawal. NYC (+ state and federal) income taxes are also included as an example.

Each simulation run uses a different randomly generated set of market returns. You can have it run 100 simulations and summarize the results, reporting on the various percentiles of outcomes after each decade.

Sample report:
```
              2030            10%           20%           50%           80%          Mean
       Investments:    $1,666,844    $1,767,942    $2,060,005    $2,339,828    $2,057,202
        Retirement:    $1,672,445    $1,977,891    $2,729,116    $3,798,156    $3,032,895
       Real estate:      $671,129      $678,578      $693,484      $709,427      $693,844

              2040            10%           20%           50%           80%          Mean
       Investments:    $2,461,642    $2,744,543    $3,320,069    $3,995,028    $3,392,655
        Retirement:    $2,723,549    $3,716,723    $6,080,778    $9,449,286    $7,191,910
       Real estate:    $1,119,091    $1,126,538    $1,143,893    $1,166,355    $1,146,240

              2050            10%           20%           50%           80%          Mean
       Investments:    $4,662,784    $5,018,233    $6,404,925    $8,116,520    $6,512,778
        Retirement:    $1,409,481    $2,623,490    $6,327,954   $16,685,415    $9,869,389
       Real estate:    $1,656,798    $1,674,842    $1,711,933    $1,751,333    $1,711,884

              2060            10%           20%           50%           80%          Mean
       Investments:    $6,589,623    $7,920,665   $10,258,782   $14,687,034   $10,852,437
        Retirement:      $403,675      $599,027    $8,124,133   $36,454,233   $20,427,453
       Real estate:    $2,008,117    $2,031,506    $2,086,502    $2,134,982    $2,085,793

              2070            10%           20%           50%           80%          Mean
       Investments:    $6,370,397    $9,237,611   $16,162,112   $22,207,417   $15,851,272
        Retirement:      $586,773    $1,003,030   $13,777,765   $57,625,401   $38,380,464
       Real estate:    $2,441,272    $2,468,178    $2,544,700    $2,624,596    $2,499,399
```

If you want to peek at the details, the complete ledgers for all accounts for a single run of the simulation get saved to the `ledgers/` directory, showing each withdraw, deposit and transfer.

```
$ head ledgers/checking
Year Mo Note                                    Amount             Tax         Balance
2021  1 Transfer from Income                $13,357.14               -      $39,357.14
2021  1 Credit card                         $-3,633.40               -      $35,723.75
2021  1 Nanny                               $-2,675.72               -      $33,048.03
2021  1 Travel                              $-1,281.24               -      $31,766.79
2021  1 Transfer to Mortgage 1A             $-1,144.63               -      $30,622.15
2021  1 Transfer to Merrill                $-10,622.15               -      $20,000.00
2021  2 Transfer from Income                $26,737.94               -      $46,737.94
2021  2 Credit card                         $-2,773.94               -      $43,964.01
2021  2 Nanny                               $-2,499.10               -      $41,464.90
```

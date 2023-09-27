# whether to buy

## expectation

-   probability of going up
-   amount to win / lose

# how much to buy

## kelly

F = P - (1-P) / R

F: % of investment (against total investment) P: probability to win R:
expected-amount-to-win / expected-amount-to-lose

# how to measure risk

## expectation - base (0)

when expectation is high and above base, it\'s low risk

## variance

higher fluctuation (of possible outcome) is higher risk initial
portfolio theory used variance as risk measurement

## consider

high variance is mitigated if long term investment when equal
expectation, lower variance is lower risk

# how much to diversify

## when not prepared

diversify, start from index fund

## goal is to focus on relatively small \# (5 or fewer)

# process

## select candidates

-   human

## for each candidate

### indicators produce predictions

each indicator might produce multiple predictions

### weight those predictions (weight on indicators)

### produce distribution (we might try different weights)

## choose what to buy

-   high expectation, low variance (how? just use expectation if hard)

## choose how much to buy

-   kelly

## evaluate current holding

### for each holding

1.  indicators evaluate holding

    we have bought this holding with this prediction data is the
    prediction still valid? can you (indicator) evaluate the current
    standing?

## decide buy / sell

With new candidates for buy, evaluations for current holdings, decide
buy / sell (2nd-level indicators)

# update process

With prediction / evaluation, evaluate indicators / 2nd-level indicators

# indicators

decision unit

## performs following (api)

### produce predictions

``` python
def predict(self, stock_id: str) -> Prediction:
    pass
```

### evaluate prediction on different time (how valid is the past prediction now?)

if we made prediction on 3month granular, after 1 month, we\'d be in
position to evaluate that prediction this is not the same as making
another 3month future prediction

``` python
def evaluate(self, stock_id: str, prediction: Prediction, evaluate_at: datetime) -> Evaluation:
    pass
```

# 2nd-level indicators

aggregate multiple (selective) indicators to produce Prediction /
Evaluation

# data

## raw data for prediction

raw data falls into following categories

-   Target data Target data is what we are trying to get, but unable to
    get perfectly It answers how much an investment is worth and how
    much we are paying for

    -   valuation (how much company value)
    -   price (how much company cost (eg, stock price))

-   Target proxy data It is not directly related to the measurement of
    target data but it is a proxy

    -   eg, company buying its own stocks can signal a new valuation

-   Environment data relavant data which affects interpretation of
    target data

    -   inflation
    -   interest rate

-   Speculation data

    -   how people perceive market (people speculation)
    -   how I perceive market (own speculation)

-   Past pattern data eg, MA trends analysis

## Prediction

-   probability of going up / expected-amount (amount is in % unit)

-   when is this prediction about

    -   prediction-horizon:
        -   when is this prediction about
        -   center and range (variance)

-   what is the nature of the prediction

    -   valuation / speculation / environment

In order to evaluate the prediction later, prediction has to show why
(on what basis) we made the prediction

## buy data

data stored when buying takes place

# Current plan (ag1)

decide if this is a good time to buy stock (index fund) so we have only
single candidate

-   decide which data to use

# [TODO]{.todo .TODO} index fund indicator {#index-fund-indicator}

## [TODO]{.todo .TODO} decide which raw data to use {#decide-which-raw-data-to-use}

## [TODO]{.todo .TODO} decide decision rule {#decide-decision-rule}

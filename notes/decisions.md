


<a id="org7e15330"></a>

# whether to buy


<a id="org5031cbe"></a>

## expectation

-   probability of going up
-   amount to win / lose


<a id="org6bf6843"></a>

# how much to buy


<a id="org2ea0d0f"></a>

## kelly

F = P - (1-P) / R

F: % of investment (against total investment)
P: probability to win
R: expected-amount-to-win / expected-amount-to-lose


<a id="org596fd82"></a>

# how to measure risk


<a id="org9d73468"></a>

## expectation - base (0)

when expectation is high and above base, it&rsquo;s low risk


<a id="org9c8ddf6"></a>

## variance

higher fluctuation (of possible outcome) is higher risk
initial portfolio theory used variance as risk measurement


<a id="orga8aba6e"></a>

## consider

high variance is mitigated if long term investment
when equal expectation, lower variance is lower risk


<a id="org623073d"></a>

# how much to diversify


<a id="org35144e0"></a>

## when not prepared

diversify, start from index fund


<a id="org95a857b"></a>

## goal is to focus on relatively small # (5 or fewer)


<a id="orgde831ec"></a>

# process


<a id="org8e8999c"></a>

## select candidates

-   human


<a id="org16f8d70"></a>

## for each candidate


<a id="orge72bad0"></a>

### indicators produce predictions

each indicator might produce multiple predictions


<a id="orgde5ff58"></a>

### weight those predictions (weight on indicators)


<a id="orgc07cbd4"></a>

### produce distribution (we might try different weights)


<a id="org51ab98e"></a>

## choose what to buy

-   high expectation, low variance
    (how? just use expectation if hard)


<a id="orga3db1d5"></a>

## choose how much to buy

-   kelly


<a id="orgab2a6df"></a>

## evaluate current holding


<a id="orgfb7cdf8"></a>

### for each holding

1.  indicators evaluate holding

    we have bought this holding with this prediction data
    is the prediction still valid? can you (indicator) evaluate the current standing?


<a id="org42384f3"></a>

## decide buy / sell

With new candidates for buy, evaluations for current holdings,
decide buy / sell (2nd-level indicators)


<a id="orgefc5994"></a>

# update process

With prediction / evaluation, evaluate indicators / 2nd-level indicators


<a id="org8fe45ba"></a>

# indicators

decision unit


<a id="orgf51a286"></a>

## performs following (api)


<a id="orgd821083"></a>

### produce predictions

    def predict(self, stock_id: str) -> Prediction:
        pass


<a id="orgfb72684"></a>

### evaluate prediction on different time (how valid is the past prediction now?)

if we made prediction on 3month granular, after 1 month, we&rsquo;d be in position to evaluate that prediction
this is not the same as making another 3month future prediction

    def evaluate(self, stock_id: str, prediction: Prediction, evaluate_at: datetime) -> Evaluation:
        pass


<a id="org568e108"></a>

# 2nd-level indicators

aggregate multiple (selective) indicators to produce Prediction / Evaluation


<a id="org012c77d"></a>

# data


<a id="orgd19ee46"></a>

## raw data for prediction

raw data falls into following categories

-   Target data
    Target data is what we are trying to get, but unable to get perfectly
    It answers how much an investment is worth and how much we are paying for
    -   valuation (how much company value)
    -   price (how much company cost (eg, stock price))

-   Target proxy data
    It is not directly related to the measurement of target data but it is a proxy
    -   eg, company buying its own stocks can signal a new valuation

-   Environment data
    relavant data which affects interpretation of target data
    -   inflation
    -   interest rate

-   Speculation data
    -   how people perceive market (people speculation)
    -   how I perceive market (own speculation)

-   Past pattern data
    eg, MA trends analysis


<a id="org3cb426e"></a>

## Prediction

-   probability of going up / expected-amount (amount is in % unit)

-   when is this prediction about
    -   prediction-horizon:
        -   when is this prediction about
        -   center and range (variance)

-   what is the nature of the prediction
    -   valuation / speculation / environment

In order to evaluate the prediction later, prediction has to show why (on what basis) we made the prediction


<a id="org9d6303a"></a>

## buy data

data stored when buying takes place


<a id="org42396fe"></a>

# Current plan (ag1)

decide if this is a good time to buy stock (index fund)
so we have only single candidate

-   decide which data to use


<a id="org04b545e"></a>

# TODO index fund indicator


<a id="org41d4c0f"></a>

## TODO decide which raw data to use


<a id="orgf54c43d"></a>

## TODO decide decision rule


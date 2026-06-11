# Carbon Arc commodity data for prediction market research

## TL;DR

We are scoping a paper that uses Carbon Arc commodity data to predict outcomes on prediction markets like Kalshi and Polymarket. We have two candidate angles in mind, listed without ranking. Neither is committed.

**Candidate A, CPI food nowcasting from the Import-Export topic.**
**Target**. Kalshi headline Consumer Price Index (CPI) contracts (KXCPI, KXECONSTATCPI series).
**Conventional inputs**. Consensus economist surveys, Cleveland Fed Inflation Nowcasting, futures-implied inflation breakevens.
**Promising alt data**. Carbon Arc's Import-Export topic, which appears to mirror food prices reported by the U.S. Bureau of Labor Statistics (BLS) and U.S. Department of Agriculture (USDA). If it surfaces ahead of the BLS release, it can act as a partial nowcast of "food at home" inside CPI.

**Candidate B, US oil production nowcasting.**
**Target**. KXBARRELS-26 (annual US oil production threshold contract).
**Conventional inputs**. U.S. Energy Information Administration (EIA) Weekly Petroleum Status Report, Baker Hughes rig counts.
**Promising alt data**. Carbon Arc has country-level crude oil production, but EIA covers the same series free and weekly, so the edge would have to come from faster cadence or cleaner cross-country panels.

We want outside input on two things. Looking at these two candidates, does either of them look promising to you, or do both look thin. And looking at the underlying material in Sections 1 through 3 (what is actually on Kalshi, what is actually inside Carbon Arc), is there a third angle we should be considering that we did not list.

## What this document is and what we want to ask

We are scoping a paper that would use Carbon Arc commodity data as input to predict prediction market outcomes on Kalshi and Polymarket. Before we commit to a direction, we want to sanity check our reading of the data and the market landscape against someone who has seen these venues from the inside.

This document is organized around three things, and we would value your reaction to each.

First, what kinds of commodity related prediction markets actually exist today on Kalshi, and which of them seem liquid enough to be worth modeling against. We pulled the cached event metadata and grouped what we saw. The summary is in Section 1.

Second, what Carbon Arc actually contains, based on sampling each topic in the CA0077 Commodity Metrics dataset. Carbon Arc's public description and the dataset's labels do not always match what is in the rows. We documented the gap. The summary is in Section 2.

Third, the angles that we are tentatively considering for the paper. None of these are decisions yet. We are sharing them so you can tell us whether the reasoning holds up, whether you would weight the candidates differently, and most importantly whether there is a direction we are missing that should be on the list. Sections 3 through 6 lay out our current draft thinking and the specific questions we have.

If something we treat as a fact below is wrong, the rest collapses, so please push back on anything that looks off.

## Section 1, the prediction market landscape we observed on Kalshi

We queried Kalshi's cached event pool (about 4,000 events) for every commodity adjacent keyword we could think of. The results sort into four clusters, plus one striking absence.

### Macro inflation markets are the largest and most active cluster

These markets resolve on macro releases from the U.S. Bureau of Labor Statistics (BLS) and Bureau of Economic Analysis (BEA), with Consumer Price Index (CPI) prints being the most active. Multiple series run monthly with many threshold contracts each.

| Series ticker | What it resolves on | Cadence |
| --- | --- | --- |
| KXCPI | Headline CPI month over month threshold | Monthly |
| KXECONSTATCPI | Headline CPI month over month, alternative thresholds | Monthly |
| KXECONSTATCPIYOY | Headline CPI year over year threshold | Monthly |
| KXECONSTATCPICORE | Core CPI month over month threshold | Monthly |
| KXECONSTATCORECPIYOY | Core CPI year over year threshold | Monthly |
| KXCOREUND | Annual core CPI under target | Annual |
| KXHIGHINFLATION | Annual peak CPI | Annual |
| KXLCPIMAXYOY | Annual inflation surge | Annual |
| KXPCECORE | Monthly Core PCE threshold | Monthly |
| KXPPIVSCPI | PPI vs CPI relative | Annual |

Headline CPI includes food and energy. Core CPI excludes both. Food and energy commodities therefore feed directly into headline contracts and only indirectly into core contracts.

### Oil markets are the second largest cluster

West Texas Intermediate (WTI) crude is the most active commodity ticker on Kalshi. Several market structures coexist.

| Series ticker | What it resolves on |
| --- | --- |
| KXWTI-26NOV03 | WTI front month settle on a fixed date (45 contracts) |
| KXWTIMAX-26DEC31 | Year end maximum WTI front month settle |
| KXWTIMIN-26DEC31 | Year end minimum WTI front month settle |
| KXWTIVSBRENT | Annual return WTI vs Brent |
| KXBARRELS-26 | US oil production barrels per day for the year |
| KXOILRIGS-26 | US oil rigs count at year end (Baker Hughes) |
| KXCRUDEEXPORTBAN-27 | US crude oil export ban policy event |

The price contracts (KXWTI, KXWTIMAX, KXWTIMIN) resolve on exchange spot. The fundamentals contracts (KXBARRELS, KXOILRIGS) resolve on the U.S. Energy Information Administration (EIA) Weekly Petroleum Status Report and Baker Hughes rig count.

### Natural gas and retail gasoline

| Series ticker | What it resolves on |
| --- | --- |
| KXNGASMAX-26DEC31 | Highest Henry hub spot in 2026 |
| KXNGASMIN-26DEC31 | Lowest Henry hub spot in 2026 |
| KXAAAGASMINTX, NY, FL, CA | State level retail gasoline price thresholds (American Automobile Association data) |

### What we did not find

The following keyword searches returned zero hits across the 4,000 event pool.

| Search keyword | Hits on Kalshi |
| --- | --- |
| soybean | 0 |
| wheat | 0 |
| corn | 0 |
| WASDE | 0 |
| USDA | 0 |
| commodity | 0 |

If this is accurate, it means there are essentially no Kalshi contracts that resolve on USDA crop reports such as the World Agricultural Supply and Demand Estimates (WASDE), grain prices, or ending stocks.

## Section 2, what Carbon Arc actually contains

There is one commodity focused dataset, CA0077 Commodity Metrics, organized into five topics.

| Topic | Nominal content | Real content from sampling |
| --- | --- | --- |
| Prices | Price series | EU Commission and USDA producer wholesale prices, weekly and monthly |
| Production | Output volumes | Mostly global dairy production (milk, butter, cheese, whole milk powder) |
| Consumption | Domestic use | Soybean and dairy consumption, mostly US, Argentina, China, Brazil |
| Stocks | Inventory | US dairy cold storage and global soybean stocks |
| Import-Export | Label is misleading | US BLS and Federal Reserve Economic Data (FRED) retail and producer prices for consumer food goods |

The "raw commodity" universe is 4,261 items. The breakdown by domain tells us what the dataset is in practice.

| Domain | Count | Composition |
| --- | --- | --- |
| Agriculture | 3,953 | Grains, livestock cuts, dairy, fish, vegetables. The bulk of the dataset. |
| Food | 211 | Processed goods (oils, wines, cheeses, frozen items) |
| Chemicals | 43 | Fertilizers (Urea, DAP, MAP, Potash), acids, vitamins |
| Materials | 37 | Paper, kraftliner, timber |
| Energy | 14 | Only 4 are actually energy. Crude oil, Henry hub natural gas, Electricity Endex, Electricity Spot. The other 10 are taxonomy errors. |
| Minerals | 3 | All three are mislabeled |

### What appears to be absent

This list matters because it rules certain angles out unless we are reading the dataset wrong.

- No exchange traded metals. No copper, aluminum, gold, silver, iron ore, lithium, nickel, zinc.
- No refined energy products. No gasoline, diesel, heating oil, coal, jet fuel.
- No vessel level shipping data accessible through the SDK. The separate CA0080 Maritime dataset claims vessel granularity in its description but every SDK access path returns errors. We are not sure whether this is an SDK limitation or whether the data is actually unavailable.
- No country level grain price series at high frequency. Wheat shows up under EU AHDB producer prices, but no soybean or corn weekly futures equivalent.

## Section 3, how we are tentatively matching Carbon Arc topics to the markets

For each Carbon Arc topic, we asked two questions. Does a Kalshi contract exist that settles on data of the same shape. And does Carbon Arc's series plausibly carry signal about that contract's resolution. The matches below are our current reading. We would value pushback on any of them.

### Import-Export topic, which seems to actually be US BLS food prices

The sample shows 100 percent US rows sourced from BLS via FRED, plus USDA producer prices.

Real sample rows.

```
Orange juice, frozen    USA   US-FRED (consumer price)   USD/lb         2.364    2021-04
Sugar, white            USA   US-FRED (consumer price)   USD/lb         0.663    2015-04
Ice cream, prepackaged  USA   US-FRED (consumer price)   USD/troy oz    0.059    2005-07
Butterfat               USA   US-USDA                    USD/lb         2.757    2023-05
Other solids            USA   US-USDA                    USD/lb         0.021    2003-03
```

Our reading is that these items are the same individual food prices that BLS aggregates into the food at home subcomponent of CPI. Food at home is roughly 8 percent of the CPI basket, and food and beverages overall sit around 14 percent.

If that reading is right, the candidate Kalshi mapping is the CPI series cluster. The hypothesis would be that Carbon Arc surfaces these prices on a cadence that gives a partial nowcast of the food at home component before BLS releases the corresponding CPI print.

The unresolved piece is whether Carbon Arc actually publishes ahead of BLS or simply mirrors it after the fact. We have not been able to verify this from the SDK alone.

### Stocks topic

Real sample rows.

```
Soybean    Canada     3,600,000  MT       2015-12
Soybean    France        58,388  MT       2024-07
Soybean    Canada     2,753,000  MT       2011-12
Butter     USA      145,098,000  Pound    2012-10
Dry whey   USA       32,832,000  Pound    2002-09
Dry whey   USA       68,314,000  Pound    2019-06
```

This is the slice of Carbon Arc that looks most like classic alt data for ag traders. Country level soybean stocks for US, Brazil, Argentina, China is the kind of series followed ahead of WASDE.

Our reading is that the Kalshi mapping is the part that fails. With no grain or WASDE contracts on Kalshi, the data quality does not matter for our use case. If you know of contracts elsewhere (Polymarket, niche venues, or upcoming Kalshi listings) where this would map, we would want to hear it.

### Crude oil and Henry hub natural gas

Carbon Arc has crude oil production at the country level (no price), and Henry hub natural gas at price (no production).

For US oil production, KXBARRELS-26 is a direct match in shape. The same data is available from EIA on a weekly cadence at no cost.

For WTI threshold contracts (KXWTI, KXWTIMAX, KXWTIMIN), Carbon Arc has no front month price.

For Henry hub spot threshold contracts (KXNGASMAX, KXNGASMIN), Carbon Arc has Henry hub price as a series. EIA publishes the same data daily for free.

Our reading is that the signal exists but offers no obvious edge over EIA, only convenience. We are not sure whether Carbon Arc adds anything (country breakdown, faster cadence, source variants) that would justify using it over EIA in a paper. If you have used both, we would value your view.

### Production topic, mostly dairy

The Production topic is 87 percent dairy across the sample. Country mix is US, Canada, UK, New Zealand, Japan, plus an EU tail.

We did not find dairy specific Kalshi markets in our search. Dairy contributes to CPI food at home indirectly, so this topic might be one feature in a multivariable CPI nowcasting model, but we do not see it as a standalone angle on its own.

### Prices topic

Sample rows.

```
Cows ddwt, D-P2          Estonia    EUR/100kg   466.07   EE - EU Commission   2025-12
Wheat, milling, other    UK         GBP/MT       93.60   UK - AHDB             2010-02
Heifers lvwt, regular    Argentina  USD/head    274.57   AR - MAG              2022-04
```

This is European livestock producer prices and a thin tail of other national reports. No Kalshi contract we saw resolves on EU producer prices, so we have no direct mapping in mind. If there is a European prediction market venue with comparable contracts, that would change the picture.

### Consumption topic

Country mix is US 44 percent, Argentina 26 percent, China 10 percent. China soybean crush is followed in commodity trading but did not appear on Kalshi in our search.

## Section 4, the angles we are tentatively considering

Two candidate directions. Listed for discussion, not in any order. Neither is a decision yet. The reason for sharing both is to make it easy to pressure-test our assumptions, and to invite a third angle that we may be missing.

Each candidate is summarized along three lines. **Target** is the prediction market contract we would try to forecast. **Conventional inputs** are what current consensus uses to predict that contract's resolution. **Promising alt data** is the slice of Carbon Arc we think could add information beyond the conventional inputs, and why.

### Candidate A, CPI food nowcasting from the Import-Export topic

**Target**. Kalshi headline CPI contracts (KXCPI, KXECONSTATCPI series), which resolve on the monthly BLS CPI print.
**Conventional inputs**. Consensus economist surveys, Cleveland Fed Inflation Nowcasting, futures-implied breakevens.
**Promising alt data**. Carbon Arc's Import-Export topic appears to mirror BLS- and USDA-sourced food prices (orange juice, sugar, butterfat, ice cream, others) at item level. If Carbon Arc surfaces these ahead of the BLS CPI release, the series acts as a partial nowcast of "food at home" (food and beverages is roughly 14 percent of the CPI basket). Food has been a frequent swing factor in monthly prints since 2022, so even a partial item-level lead could be material on close prints.

### Candidate B, US oil production nowcasting

**Target**. KXBARRELS-26, the annual US oil production threshold contract.
**Conventional inputs**. EIA Weekly Petroleum Status Report, Baker Hughes rig counts, drilled-but-uncompleted (DUC) well inventory.
**Promising alt data**. Carbon Arc has country-level crude oil production. EIA covers the same series at higher frequency for free, so the edge here would only come from Carbon Arc surfacing the data faster or with cleaner cross-country panels. We have not found evidence either is true.

## Section 5, specific questions we want your input on

1. Looking at Candidate A and Candidate B as we have framed them, do either of the underlying mechanisms have a flaw we have missed?
2. Looking at Sections 1 through 3, is there a paper angle we have not framed that someone with this domain experience would point us toward?

Anything you push back on at the fact level or at the framing level would be useful.

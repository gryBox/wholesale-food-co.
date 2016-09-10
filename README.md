# Build a Data Analysis Tool using Bokeh

## Intended Audience:
Developer(s) who want to build a robust, custom data analysis tool for the web.

## Run The Example:
`python 3.5>`
[here](https://github.com/adam-hubbell/wholesale-food-co./blob/master/fruit_market/how_to_run_the_server.txt)

## Main Features:
- System centered around analysts development workflow
- No data duplication for the different interactive tools
- Data frequency limited 'only' by data model(s) computation time
- Each Bokeh app is independent, but follows a load data 'api' - Non developers can easily load new bokeh apps into production 
  1. At their own pace
  2. Without fear of crashing the rest of the app

## Experience Needed:
Some minimal coding experience and lots of curiosity. We were a team of 3... 2 members of our team had < 1 month experience in python

## Time to Build:
It took us 3 months.  Knowing what we know now, it would probably take about 1.5 months.

## Main Packages:
| Python Package | Use                            |
| -------------- | ------------------------------ |
| tornado        | web server                     |
| flask          | web pages                      |
| sqlalchemy     | connecting to databases        |
| pandas         | dataframes                     |
| bokeh          | interactive data visualizations|

## Story Line:
This is an example use case for an Wholesale Food Company whose business is to find fruit of varying quality around the world at the best price for:

1. **Customers** (Restaurants, Supermarkets) who call ...

2. The company's **Food Shoppers** who use proprietary analytic tools created by ...

3. **Analysts** that allow the Food Shoppers to have informed conversations with ...

4. **Regional buyers** and **Purveyors** about Food Prices the Customer wants to buy

![System Overview](https://github.com/gryBox/wholesale-food-co./blob/master/System Overview.png)

Note: All the data is fake and we have no idea if this is how the food industry works.

## Data Pipeline:
The system processes about 260 million rows of a *fully normalized data* or ~10 gigs in memory. When the analyst and web server receive the data, it blows up to 44 gigs and then shrinks back to *megabytes* on the bokeh app.

![System Overview](https://github.com/gryBox/wholesale-food-co./blob/master/Dataflow.png)

## Next Steps
- [distributed](http://distributed.readthedocs.io/en/latest/) 
- [Luigi](https://luigi.readthedocs.io/en/stable/)

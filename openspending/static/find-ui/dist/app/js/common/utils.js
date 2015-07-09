(function() {
    window.utils = {};

    window.flipCardEvent = function() {

        $(".flip").click(function() {



            if (window.expandedCategory) {
                window.expandedCategory = false;
                return;
            }

            if (window.clickedIndicator) {
                window.clickedIndicator = false;
                return;
            }

            $(".flip").css("z-index", 10);
            $(this).css("z-index", 1000);
            $(".flip").find("div.list-group").removeClass("shadow");

            $(this).find("div.list-group").addClass("shadow");

            var isFlipped = $(this).find(".card").hasClass("flipped");

            $(".flip").find(".card").removeClass("flipped");
            $(".flip").removeClass("flippedCol");
            //- $(".list-group").css("display": "none");

            if (isFlipped) {
                //$(this).find(".card").removeClass("flipped");
                // $(this).find(".list-group").removeClass("show-me");

            } else {
                $(this).find(".card").addClass("flipped");
                $(this).addClass("flippedCol");

                //$(this).find(".list-group").addClass("show-me");
            }
            return true;
        });
    }

    window.getHashParams = function() {

        var hashParams = {};
        var e,
            a = /\+/g, // Regex for replacing addition symbol with a space
            r = /([^&;=]+)=?([^&;]*)/g,
            d = function(s) {
                return decodeURIComponent(s.replace(a, " "));
            },
            q = window.location.hash.substring(1);

        while (e = r.exec(q))
            hashParams[d(e[1])] = d(e[2]);

        return hashParams;
    }

    window.updateHash = function(hashObj) {

        var result = decodeURIComponent($.param(hashObj));
        window.location.hash = result; //console.log("fdfsd");
    }


    window.bindIndicators = function(response, model) {
        //debugger;
        var categoriesAll = response.data.categories;
        var subcategoriesAll = response.data.subcategories;
        var sourcesAll = response.data.sources;
        var indicatorsAll = response.data.indicators;

        var categoriesModel = [];
        var sourcesModel = [];
        var indicatorsModel = [];

        //Sort out Categories
        for (var cat in categoriesAll.data) {

            var isOnlyCategory = function(indicatorId) {
                return indicatorsAll.data[indicatorId].subcategory === "None";
            }

            var isSubCategory = function(indicatorId) {
                return indicatorsAll.data[indicatorId].subcategory != "None";
            }

            var makeIndicator = function(indicatorId) {
                var sourceId = _.get(indicatorsAll, 'data[indicatorId].source');
                var sourceLabel = _.get(sourcesAll, 'data[sourceId].label');

                var cloneIndicator = _.clone(indicatorsAll.data[indicatorId], true);

                cloneIndicator.source = sourceLabel;
                cloneIndicator.id = indicatorId;
                cloneIndicator.selected = false;

                return cloneIndicator;
            }

            var indicatorsIdsInCategory = _.filter(categoriesAll.data[cat].indicators, _.negate(isSubCategory));

            var indicatorsIdsInSubCategory = _.filter(categoriesAll.data[cat].indicators, _.negate(isOnlyCategory));

            var indicatorsInCategory = _.map(indicatorsIdsInCategory, makeIndicator);
            var indicatorsInSubCategory = _.map(indicatorsIdsInSubCategory, makeIndicator);

            //arrange subcategories in order
            var subcategories = [];

            var subcategoriesTracker = [];

            _.forEach(indicatorsInSubCategory, function(indicator) {

                var subCatIndex = _.indexOf(subcategoriesTracker, indicator.subcategory);

                if (subCatIndex < 0) {
                    //debugger;
                    var newSubCategory = {
                        "id": indicator.subcategory,
                        "label": subcategoriesAll.data[indicator.subcategory].label,
                        "indicators": [indicator],
                        "selected": false
                    }
                    subcategoriesTracker.push(indicator.subcategory);
                    subcategories.push(newSubCategory);
                } else {
                    subcategories[subCatIndex].indicators.push(indicator);
                }

            });

            if (subcategories.length > 0 && indicatorsInCategory.length > 0) {
                var generalSubCategory = {
                    "label": "General",
                    "indicators": indicatorsInCategory,
                    "selected": false
                }
                subcategories.unshift(generalSubCategory);
            }


            //debugger;
            var newCategory = {
                "label": categoriesAll.data[cat].label,
                "length": categoriesAll.data[cat].indicators.length,
                "indicators": indicatorsInCategory,
                "subcategories": subcategories
            }



            categoriesModel.push(newCategory);

        }
        //debugger;
        //Sort out Sources
        for (var src in sourcesAll.data) {

            var indicatorsInSource = _.map(sourcesAll.data[src].indicators, function(indicatorId) {

                var categoryId = _.get(sourcesAll, 'data[indicatorId].category');
                var categoryLabel = _.get(sourcesAll, 'data[categoryId].label');

                var cloneIndicator = _.clone(indicatorsAll.data[indicatorId], true);

                cloneIndicator.source = categoryLabel;
                cloneIndicator.id = indicatorId;
                cloneIndicator.selected = false;
                return cloneIndicator;

            });

            var newSource = {
                "label": sourcesAll.data[src].label,
                "length": sourcesAll.data[src].indicators.length,
                "indicators": indicatorsInSource
            }

            sourcesModel.push(newSource);

        }
        //debugger;
        //Get the actual categories and sources
        for (var ind in indicatorsAll.data) {

            var newIndicator = indicatorsAll.data[ind];
            var sourceId = newIndicator.source;
            var categoryId = newIndicator.category;


            newIndicator.source = _.get(sourcesAll, 'data[sourceId].label');
            newIndicator.category = _.get(categoriesAll, 'data[categoryId].label');
            newIndicator.id = ind;
            newIndicator.selected = false;
            //newIndicator.popup = newIndicator.source + "<br>" + newIndicator.category;
            indicatorsModel.push(newIndicator);



        }
        // debugger;

        model.categoriesModel(categoriesModel);
        model.sourcesModel(sourcesModel);
        model.indicatorsModel(indicatorsModel);
        model.indicatorsModelMaster(_.clone(indicatorsModel, true));
    }

    window.bindCountries = function(response, model) {



        var countryGroupings = _.clone(model.countryGroupings(), true);

        //push regions in country groupings
        _.forEach(countryGroupings, function(countryGroup, i) {

            var groupId = countryGroup.id;
            countryGroup.selected = false;
            countryGroup.geounit = groupId + ":all";

            if (countryGroup.id != "all") {
                var trackRegion = [];
                _.forEach(response.data, function(country) { //for each Country

                    //find level this country belongs to in this group
                    var region = country.regions[groupId];
                    var regionObj = {
                        id: region,
                        label: region,
                        geounit: groupId + ":" + region,
                        countries: [],
                        selected: false
                    }

                    if (_.indexOf(trackRegion, region) < 0) {
                        trackRegion.push(region);
                        //debugger;
                        countryGroup.regions.push(regionObj);
                    }

                });
            } else {

                countryGroup.regions.push({ //push a region called All for All
                    id: "all",
                    label: "All Countries",
                    countries: [],
                    selected: false
                });

            }


        });

        //push country in regions
        _.forEach(countryGroupings, function(countryGroup, i) {

            _.forEach(countryGroup.regions, function(region) {

                _.forEach(response.data, function(country) { //for each Country
                    var regionId = region.id;

                    var c = countryGroup;

                    if (country.regions[countryGroup.id] == regionId || regionId == "all") {
                        country.selected = false;
                        country.id = country.iso_a2;
                        region.countries.push(country);
                    }

                });

            });

        });



        model.countryGroupings.removeAll();

        _.forEach(countryGroupings, function(countryGroup, i) {
            model.countryGroupings.push(countryGroup);
        });


        _.forEach(response.data, function(country) {
            country.selected = false;
        });


        model.countriesModel(response.data);
        model.countriesModelMaster(_.clone(response.data, true));

        model.activeGroup(countryGroupings[0]);
    }

    window.highlightOnMap = function(model, all) {

        //var all = false;
        //if all then select all countries in countriesModel, else activeCountries

        var countries = model.countriesModel();
        var features = [];
        if (model.activeCountries().length > 0) {
            countries = model.activeCountries();
        }

        var countriesGeounit = _.map(countries, function(country) {
            return country.label;
        });


        var style = function(feature) {

                if (_.indexOf(countriesGeounit, feature.properties.sovereignt) >= 0) {

                    var polygon = L.multiPolygon(feature.geometry.coordinates);

                    features.push(polygon);
                    return {
                        weight: 2,
                        opacity: 1,
                        color: 'white',
                        dashArray: '3',
                        fillOpacity: 0.5,
                        fillColor: '#FF0000'
                    };
                } else {
                    return {
                        weight: 2,
                        opacity: 0,
                        color: 'white',
                        dashArray: '3',
                        fillOpacity: 0.0,
                        fillColor: '#666666'
                    };
                }
            }
            // debugger;
        window.map.removeLayer(geoJsonLayers["sovereignt"]);

        function onEachFeature(feature, layer) {
            // does this feature have a property named popupContent?
            if (feature.properties) {
                layer.bindPopup(feature.properties.sovereignt);
            }
        }

        geoJsonLayers["sovereignt"] = L.geoJson(window.countriesJson, {
            onEachFeature: onEachFeature,
            style: style
        });

        return;

        setTimeout(function() {

            map.addLayer(geoJsonLayers["sovereignt"]);
            /*L.geoJson(geoJsonLayers["sovereignt"].toGeoJSON(), {
                style: style,
                onEachFeature: onEachFeature
            }).addTo(window.map);*/

            var group = new L.featureGroup(features);
            var bounds = group.getBounds();


            var southWestLng = bounds._southWest.lng;
            var northEastLng = bounds._northEast.lng;

            bounds._southWest.lng = bounds._southWest.lat;
            bounds._southWest.lat = southWestLng;
            bounds._northEast.lng = bounds._northEast.lat;
            bounds._northEast.lat = northEastLng;


            map.fitBounds(bounds);
        }, 0);

    }

    window.utils.prepareHighchartsJson = function(data, statsData, indicatorsMeta, type, indicators, group, region, groupByRegion) {

        //var defaultCountries = ["australia", "new zealand", "sweden", "germany", "france", "ghana", "kenya", "south africa", "bangladesh", "pakistan", "cambodia"];
        //var defaultVisibleCountries = ["australia", "germany", "kenya", "cambodia"];

        var cells = data.cells;
        //debugger;
        var statsCells = statsData.cells;
        var indicatorId = indicators[0];
        var title = indicators[0];
        var groupId = group;
        //var cutBy = "name";
        var dataType = "avg"; //sum,avg
        var multiVariate = indicators.length > 1; //eligible for scatter plot
        // var seriesAverage = [];
        var dataByYear = [];

        var titleArray = _.map(indicatorsMeta, function(meta) {
            return meta[0].label;
        });

        //
        /*switch (true) {
            case (groupId == "all" && !groupByRegion):
                // debugger;
                cutBy = "sovereignt";
                break;
            default:
                // debugger;
                cutBy = groupId;
                break;
        }*/
        //debugger;
        /*if (!multiVariate && region.length > 0 && !groupByRegion) {
            cutBy = "sovereignt"
        }*/

        //debugger;
        /*var timeCell = {};
        _.forEach(data.cell, function(c) {
            if (c.hierarchy == "time") {
                timeCell = c;
            }
        });*/

        var fromYear = 1990; //timeCell.from[0];
        var toYear = 2015; //timeCell.to[0];
        /*debugger;
        if (type == "bar") {
            debugger;
            // fromYear = parseInt(toYear);
            toYear = parseInt(fromYear);
        }*/
        var categories = [];

        for (var i = fromYear; i <= toYear; i++) {
            categories.push(parseInt(i));
        }

        var series = {
            // "Global Minimum": [],
            // "Global Maximum": [],
            // "Global Average": [],
        };


        //Add stats to series

        /*_.forEach(statsCells, function(c) {
            //(c["geometry__time"] >= fromYear) && (c["geometry__time"] <= toYear) &&
            //if ((groupId == "all" || c["geometry__country_level0." + groupId] == region)) {
            series["Global Minimum"].push([c["geometry__time"], c[indicatorId + "__amount_min"]]);
            series["Global Maximum"].push([c["geometry__time"], c[indicatorId + "__amount_max"]]);
            series["Global Average"].push([c["geometry__time"], c[indicatorId + "__amount_avg"]]);
            // }
        });*/

        //debugger;
        var seriesArray = [];

        //debugger;
        //debugger;

        _.forEach(cells, function(c) {
            dataByYear[c.year.toString()] = [];
            series[c.region] = []
        });

        _.forEach(cells, function(c) {
            series[c.region].push([c.year, c[indicatorId + "__amount_" + dataType]]);
            dataByYear[c.year].push(c[indicatorId + "__amount" + dataType]);
        });

        /*debugger;

        if (multiVariate) { // && region.length > 0 && (groupBy == "indicators")

            _.forEach(indicators, function(indicator) {
                series[indicator] = []
            });
            //indicatorId = "gdp_per_capita";
            _.forEach(cells, function(c) {
                // if ((c["geometry__time"] >= fromYear) && (c["geometry__time"] <= toYear)) {
                //rada
                _.forEach(indicators, function(indicator) {
                    //debugger;
                    if (c["geometry__country_level0." + cutBy] == region) {

                        series[indicator].push([c["geometry__time"], c[indicator + "__amount_" + dataType]])
                    }
                });

                //series[c["geometry__country_level0." + cutBy]].push();
                // }
            });
            //debugger;
        }

        //debugger;
        if (!multiVariate || region.length == 0) {
            //debugger;
            //TODO : do this in one loop
            _.forEach(cells, function(c) {
                dataByYear[c["geometry__time"].toString()] = [];
                series[c["geometry__country_level0." + cutBy]] = []
            });
            //indicatorId = "gdp_per_capita";
            _.forEach(cells, function(c) {
                //if ((c["geometry__time"] >= fromYear) && (c["geometry__time"] <= toYear)) {
                //rada
                //debugger;
                series[c["geometry__country_level0." + cutBy]].push([c["geometry__time"], c[indicatorId + "__amount_" + dataType]]);
                dataByYear[c["geometry__time"]].push(c[indicatorId + "__amount" + dataType]);
                // }
            });

            // for (var year in dataByYear) {
            //     var total = _.reduce(dataByYear[year], function(total, n) {
            //         return total + n;
            //     });
            //     var average = total / dataByYear[year].length;
            //     seriesAverage.push([parseInt(year), average]);
            // }

        }*/


        var counter = 1;
        var countriesArr = [];
        for (var countryName in series) {
            var visible = false;
            // if (defaultVisibleCountries.indexOf(countryName) > -1) {
            visible = true;
            //  }
            //window.averageSeries = series[countryName];
            // if (defaultCountries.indexOf(countryName) > -1) {
            seriesArray.push({
                name: countryName,
                data: series[countryName],
                visible: counter > 3 ? true : false,
                zIndex: counter++
            });

            countriesArr.push(countryName);


            // }
        }

        seriesArray[0].zIndex = seriesArray.length + 1;
        seriesArray[1].zIndex = seriesArray.length + 2;
        seriesArray[2].zIndex = seriesArray.length + 3;




        //debugger;

        var chartObj = {

            type: type
        };

        if (type == "radar") {
            chartObj.polar = true;
            chartObj["type"] = "line";
        }

        var json = {
            chart: chartObj,
            title: {

                text: titleArray.join(" & "),
                x: -20
            },
            subtitle: {

                text: titleArray.join(" & "),
                x: -20
            },
            xAxis: {
                //categories: categories
                title: {
                    enabled: true,
                    text: ''
                },
                startOnTick: true,
                endOnTick: true,
                showLastLabel: true
            },
            yAxis: {
                title: {
                    text: ''
                },
                plotLines: [{
                    value: 0,
                    width: 0.25,
                    color: '#FFFFCC'
                }]
            },
            tooltip: {
                valueSuffix: ''
            },
            legend: {
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'middle',
                borderWidth: 0,
                width: 200,
                itemWidth: 100
            },
            series: seriesArray
        }

        var jsonScatter = {
            chart: {
                type: 'scatter',
                zoomType: 'xy'
            },
            title: {
                text: 'Height Versus Weight of 507 Individuals by Gender'
            },
            subtitle: {
                text: 'Source: Heinz  2003'
            },
            xAxis: {
                title: {
                    enabled: true,
                    text: 'Height (cm)'
                },
                startOnTick: true,
                endOnTick: true,
                showLastLabel: true
            },
            yAxis: {
                title: {
                    text: 'Weight (kg)'
                }
            },
            legend: {
                layout: 'vertical',
                align: 'left',
                verticalAlign: 'top',
                x: 100,
                y: 70,
                floating: true,
                backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF',
                borderWidth: 1
            },
            plotOptions: {
                scatter: {
                    marker: {
                        radius: 5,
                        states: {
                            hover: {
                                enabled: true,
                                lineColor: 'rgb(100,100,100)'
                            }
                        }
                    },
                    states: {
                        hover: {
                            marker: {
                                enabled: false
                            }
                        }
                    },
                    tooltip: {
                        headerFormat: '<b>{series.name}</b><br>',
                        pointFormat: '{point.x} cm, {point.y} kg'
                    }
                }
            },
            series: [{
                name: 'Country A',
                color: 'rgba(223, 83, 83, .5)',
                data: [
                    [2010, 51.6],
                    [2011, 59.0]
                ]

            }, {
                name: 'Country B',
                color: 'rgba(119, 152, 191, .5)',
                data: [
                    [2010, 65.6],
                    [2011, 71.8]
                ]
            }]
        }

        //debugger;
        return {
            highcharts: json
            //average: seriesAverage
        };
    }

}())
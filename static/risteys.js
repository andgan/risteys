// Main histogram plot

function hist_chart(data, hist_chart_width, hist_chart_height, chart_margin, id) {

    var x = d3.scaleBand()
        .rangeRound([0, hist_chart_width])
        .padding(0.1)
        .domain(data.map(function(d) { return d.comorbidevent; }));

    var y = d3.scaleLinear()
        .range([hist_chart_height, 0])
        .domain([0, d3.max(data, function(d) { return d.RR; })]);

    var tip = d3.tip()
        .attr('class', 'd3-tip')
        .html(function(d) { 
            return "<p align='center' > <strong>" + d.label + "</strong></p>" +
                    "<p> <strong>N with </strong>" + d.comorbidevent + ": " + d.count_a + "</p>" +
                    "<p> <strong>With </strong>" + d.comorbidevent + ": " + d.count_a_count_ab + "</p>" +
                    "<p> <strong>Without </strong>" + d.comorbidevent + ": " + d.count_c_count_cd + "</p>" +
                    "<p> <strong>P: </strong>" + d.signlabel + "</p>"
             });

    var xAxis = d3.axisBottom(x);

    var yAxis = d3.axisLeft(y);


    var svg = d3.select(id)
        .attr("width", hist_chart_width)
        .attr("height", hist_chart_height)
        .append("g")
        .attr('id', 'inner_graph')
        .attr("transform", "translate(" + chart_margin.left + "," + chart_margin.top + ")");

    svg.call(tip);

    svg.selectAll("bar")
        .data(data, function(d){return d.indexkey;})
        .enter()
        .append("rect")
        .attr("class", "hist_bar")
        .attr("x", function(d) { return x(d.comorbidevent); })
        .attr("y", function(d) { return y(d.RR); })
        .attr("width", x.bandwidth())
        .attr("height", function(d) { return (hist_chart_height - y(d.RR)); })
        .on('mouseover', tip.show)
        .on('mouseout', tip.hide)

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + hist_chart_height + ")")
        .call(xAxis);
    
    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis);

    svg.append("text") 
      .attr("id", "xlabel")             
      .attr("transform",
            "translate(" + (hist_chart_width/2) + " ," + (hist_chart_height + chart_margin.top + 20) + ")")
      .style("text-anchor", "middle")
      .text("Comorbid ICD code");

    svg.append("text")
      .attr("id", "ylabel")   
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - chart_margin.left)
      .attr("x",0 - (hist_chart_height / 2))
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .text("Hazard Ratio"); 

}






function change_hist_chart(data, hist_chart_width, hist_chart_height, chart_margin, id) {

    
    var x = d3.scaleBand()
        .rangeRound([0, hist_chart_width])
        .padding(0.1)
        .domain(data.map(function(d) { return d.comorbidevent; }));

    var y = d3.scaleLinear()
        .range([hist_chart_height, 0])
        .domain([0, d3.max(data, function(d) { return d.RR; })]);

    var tip = d3.tip()
        .attr('class', 'd3-tip')
        .html(function(d) { 
            return "<p align='center'> <strong>" + d.label + "</strong></p>" +
                    "<p> <strong>N with </strong>" + d.comorbidevent + ": " + d.count_a + "</p>" +
                    "<p> <strong>With </strong>" + d.comorbidevent + ": " + d.count_a_count_ab + "</p>" +
                    "<p> <strong>Without </strong>" + d.comorbidevent + ": " + d.count_c_count_cd + "</p>" +
                    "<p> <strong>P: </strong>" + d.signlabel + "</p>"
             });

    var xAxis = d3.axisBottom(x);

    var yAxis = d3.axisLeft(y);

    
    var svg = d3.select(id).select('#inner_graph');

    svg.call(tip);

    var svg2 = svg.selectAll("rect")
        .data(data, function(d){return d.indexkey;})

    svg2.exit().remove();

    svg2.enter().append("rect").attr("class", "hist_bar")
        .merge(svg2)
        .attr("x", function(d) { return x(d.comorbidevent); })
        .attr("y", function(d) { return y(d.RR); })
        .attr("width", x.bandwidth())
        .attr("height", function(d) { return hist_chart_height - y(d.RR); })
        .on('mouseover', tip.show)
        .on('mouseout', tip.hide)

    var yAxis = d3.axisLeft(y);

    svg.select(".y.axis")
        .transition()
        .duration(200)
        .call(yAxis);

    var xAxis = d3.axisBottom(x);

    svg.select(".x.axis")
        .transition()
        .duration(200)
        .call(xAxis);




    d3.select("#ndtext").remove()

    if (d3.select("#xlabel").empty())
    {

    svg.append("text") 
      .attr("id", "xlabel")             
      .attr("transform",
            "translate(" + (hist_chart_width/2) + " ," + (hist_chart_height + chart_margin.top + 20) + ")")
      .style("text-anchor", "middle")
      .text("Comorbid ICD");

    svg.append("text")
      .attr("id", "ylabel")   
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - chart_margin.left)
      .attr("x",0 - (hist_chart_height / 2))
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .text("Hazard Ratio"); 
    }

    if (data.length===0)
    {
        svg.append("text")
          .attr("id", "ndtext")         
          .attr("transform",
            "translate(" + (hist_chart_width/2) + " ," + (hist_chart_height - 80) + ")")
          .style("font-size", "26px")
          .style('font-weight', 'bold')
          .style("text-anchor", "middle")
          .style('text-color', '#525252')
          .text("No data available");

          d3.select("#xlabel").remove()
          d3.select("#ylabel").remove()
    }


      
}



function time_chart(data, hist_chart_width, hist_chart_height, chart_margin, id) {


    var x = d3
            .scaleTime()
            .range([0, hist_chart_width]);
            
    var y = d3.scaleLinear()
            .range([hist_chart_height, 0]);



    var svg = d3.select(id)
        .attr("width", hist_chart_width)
        .attr("height", hist_chart_height)
        .append("g")
        .attr('id', 'inner_graph')
        .attr("transform", "translate(" + chart_margin.left + "," + chart_margin.top + ")");


    var parseTime = d3.timeParse("%Y");

    var valueline = d3.line()
         .x(function(d) { return x(d.year); })
         .y(function(d) { return y(d.incidence); });

    data.map(function(d) {
        d.year = parseTime(d.year)
        d.incidence = +d.incidence
       });

    y.domain([0, d3.max(data, function(d) { return d.incidence; })]);
    x.domain(d3.extent(data, function(d) { return d.year; }));


    svg.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "steelblue")
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round")
      .attr("stroke-width", 1.5)
      .attr("d", valueline);


    svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + hist_chart_height + ")")
      .call(d3.axisBottom(x))

    svg.append("g")
      .attr("class", "y axis")
      .call(d3.axisLeft(y))


    svg.append("text")           
      .attr("transform",
            "translate(" + (hist_chart_width/2) + " ," + (hist_chart_height + chart_margin.top + 20) + ")")
      .style("text-anchor", "middle")
      .text("Year");

    svg.append("text")
      .attr("id", "ylabel2")
      .attr("transform", "rotate(-90)")
      .attr("y", -5 - chart_margin.left)
      .attr("x",0 - (hist_chart_height / 2))
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .text("Incidence proportion"); 


}




function time_chart_change(data, type, hist_chart_width, hist_chart_height, chart_margin, id) {


    var x = d3
            .scaleTime()
            .range([0, hist_chart_width]);
            
    var y = d3.scaleLinear()
            .range([hist_chart_height, 0]);


    var svg = d3.select(id).select('#inner_graph');


    if (type=="incidence"){
    var valueline = d3.line()
         .x(function(d) { return x(d.year); })
         .y(function(d) { return y(d.incidence); });
    y.domain([0, d3.max(data, function(d) { return d.incidence; })]);
    }

    if (type=="n_events"){
    var valueline = d3.line()
         .x(function(d) { return x(d.year); })
         .y(function(d) { return y(d.n_events); });
    y.domain([0, d3.max(data, function(d) { return d.n_events; })]);
    }

    x.domain(d3.extent(data, function(d) { return d.year; }));


    svg.selectAll("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "steelblue")
        .attr("stroke-linejoin", "round")
        .attr("stroke-linecap", "round")
        .attr("stroke-width", 1.5)
        .attr("d", valueline);


    svg.select(".y.axis")
        .transition()
        .duration(200)
        .call(d3.axisLeft(y));

    svg.select(".x.axis")
        .transition()
        .duration(200)
        .call(d3.axisBottom(x));



    d3.select("#ylabel2").remove()

    if (type=="incidence")
    {

    svg.append("text")
      .attr("id", "ylabel2")   
      .attr("transform", "rotate(-90)")
      .attr("y", -5 - chart_margin.left)
      .attr("x",0 - (hist_chart_height / 2))
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .text("Incidence proportion"); 
    }

    else 
    {

    svg.append("text")
      .attr("id", "ylabel2")   
      .attr("transform", "rotate(-90)")
      .attr("y", -5 - chart_margin.left)
      .attr("x",0 - (hist_chart_height / 2))
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .text("Number of events"); 
    }

}



function map_chart(data,map_chart_width, map_chart_height, map_margin, id) {



    var svg = d3.select(id)
        .attr("width", map_chart_width)
        .attr("height", map_chart_height)
        .append("g")


    var color=d3.scaleQuantize()
    .range(["rgb(255, 255, 255)","rgb(237,248,233)","rgb(186,228,179)","rgb(116,196,118)","rgb(49,163,84)","rgb(0,109,44)"])
    .domain([0,100]);


    var projection = d3.geoMercator()
      //.scale((1 << 22) / 2 / Math.PI)
      .scale(1500)
      .translate([map_chart_width / 2, map_chart_height / 2])
      .center([-3.208320099999997,53.8130752])
      //.translate([50, 700])


    var path = d3.geoPath()
      .projection(projection);


    var div2 = d3.select("body").append("div2");
    //.attr("class", "tooltip")
    //.style("opacity", 0);


    var tip = d3.tip()
    .attr('class', 'd3-tip-map')
    .html(function(d) { 
            if (d.properties.centerV)
            {
            return "<p> <strong> Assessment center: </strong>" + d.properties.centerV + "</p>" +
            "<p> <strong> N. events: </strong>" + d.properties.n_eventV + "</p>" +
            "<p> <strong> % events/total recruited: </strong>" + (d.properties.value*100).toFixed(2) + "%</p>"
            }
            else
            {
            return "<p> <strong> No assessment center in this region </strong> </p>"
            }
             });

    svg.call(tip);


    // /Users/andreaganna/flaskapp/node_modules/geojson-precision/bin/geojson-precision -p 2 /Users/andreaganna/flaskapp/app/static/nuts2.geojson /Users/andreaganna/flaskapp/app/static/eng_sco_simple.geojson


    d3.json("/static/eng_sco_simple.geojson", function(err, geojson) {

            color.domain([d3.min(data,function(d){return d.prop_on_total;}),d3.max(data,function(d){return d.prop_on_total;})]);
            for(var j=0;j<geojson.features.length;j++){
            geojson.features[j].properties.value=0.00000001;}
            for(var i=0;i<data.length;i++){
                var dataState=data[i].NUTS2;
                var ratioV=parseFloat(data[i].prop_on_total);
                var n_eventV=parseInt(data[i].n_with_event);
                var centerV=data[i].center;
                for(var j=0;j<geojson.features.length;j++){
                  var jsonState=geojson.features[j].properties.NUTS212CD;
                    if(dataState==jsonState){
                      geojson.features[j].properties.value=ratioV;
                      geojson.features[j].properties.n_eventV=n_eventV;
                      geojson.features[j].properties.centerV=centerV;break;}
                    }
                  
                  }



            var features = geojson.features;

            //console.log(features)
            svg.selectAll("path")
                  .data(features)
                  .enter().append('path')
                  .attr('d', path)
                  .style("stroke","rgb(0,109,44)")
                  .style('fill', setNormalColor)
                  .on("mouseover",function(d){
                    tip.show(d)
                    d3.select(this)
                       .style("fill", "orange");
                   })
                  .on("mouseout", function(d) {
                    tip.hide()
                   d3.select(this)
                     .style("fill", setNormalColor(d));   
                   });
   
    });



var setNormalColor=function(d){var value=d.properties.value;if(value){return color(value);}else{return"rgb(255, 255, 255)";}};


}




function hist_chart_bins(data, hist_chart_width, hist_chart_height, chart_margin, xlab, id) {


    var x = d3.scaleBand()
        .rangeRound([0, hist_chart_width])
        .padding(0)
        .domain(data.map(function(d) { return d.mid; }));

    var y = d3.scaleLinear()
        .range([hist_chart_height, 0])
        .domain([0, d3.max(data, function(d) { return d.count/1000; })]);


    var xAxis = d3.axisBottom(x);

    var yAxis = d3.axisLeft(y);


    var svg = d3.select(id)
        .attr("width", hist_chart_width)
        .attr("height", hist_chart_height)
        .append("g")
        .attr('id', 'inner_graph')
        .attr("transform", "translate(" + chart_margin.left + "," + chart_margin.top + ")");


    svg.selectAll("bar")
        .data(data)
        .enter()
        .append("rect")
        .attr("class", "hist_bar_small")
        .attr("x", function(d) { return x(d.mid); })
        .attr("y", function(d) { return y(d.count/1000); })
        .attr("width", x.bandwidth())
        .attr("height", function(d) { return (hist_chart_height - y(d.count/1000)); })

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + hist_chart_height + ")")
        .call(xAxis)
    .selectAll("text")
        .attr("y", 0)
        .attr("x", 9)
        .attr("dy", ".35em")
        .attr("transform", "rotate(45)")
        .style("text-anchor", "start");
    
    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis);

    svg.append("text") 
      .attr("id", "xlabel")   
      .attr("transform",
            "translate(" + (hist_chart_width/2) + " ," + (hist_chart_height + chart_margin.top + 20) + ")")
      .style("text-anchor", "middle")
      .text(xlab);

    svg.append("text")
      .attr("id", "ylabel")   
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - chart_margin.left)
      .attr("x",0 - (hist_chart_height / 2))
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .text("Participants (in 000's)"); 


}




function add_line_to_hist_chart_bins(data, position, name_m, name_l, name_u, label,meanlab,hist_chart_width, hist_chart_height, chart_margin,id) {
    //Takes dataset (for range) and datapoint and draws line in container
    //If line is already in container, transitions to new line
    var low_value = d3.min(data, function (d) { return d.mid; });
    var high_value = d3.max(data, function (d) { return d.mid; });


    xscale = d3.scaleLinear()
            .domain([low_value, high_value])
            .range([0, hist_chart_width]);

    x = function(d,indvalue) {
        var pos;
        if (d[indvalue] > high_value) {
            pos = xscale(high_value);
        } else if (d[indvalue] < low_value) {
            pos = xscale(low_value);
        } else {
            pos = xscale(d[indvalue]);
        }
        return pos;
    };

    var tip = d3.tip()
      .attr('class', 'd3-tip-small')
      .html(function(d) { 
          return "<p> Mean[C.I.]: " + d[label] + "</p>" +
                 "<p> Mean in UKBB: " + meanlab + " </p>"
           });

    var svg = d3.select(id).select('#inner_graph');

    svg.call(tip);

    var lines = svg.selectAll(".line")
                .data([position])
                .enter().append("g")
                .attr("class", "line");
    //console.log(lines)
    lines.append('line')
            .attr("x1", function(d) { return x(d,name_m); })
            .attr("x2", function(d) { return x(d,name_m); })
            .attr("y1", hist_chart_height)
            .attr("y2", 0)
            .attr("stroke-width", 2)
            .attr("stroke", "red")
    // hidden line to increase clickable area
    lines.append('line')
            .attr("x1", function(d) { return x(d,name_m); })
            .attr("x2", function(d) { return x(d,name_m); })
            .attr("y1", hist_chart_height)
            .attr("y2", 0)
            .attr("stroke-width", 15)
            .attr("stroke", "red")
            .attr("opacity", 0)
            .on('mouseover', tip.show)
            .on('mouseout', tip.hide);
    lines.append('line')
            .attr("x1", function(d) { return x(d,name_l); })
            .attr("x2", function(d) { return x(d,name_l); })
            .attr("y1", hist_chart_height)
            .attr("y2", 0)
            .attr("stroke-width", 2)
            .attr("stroke", "red")
            .style("stroke-dasharray", "4,4");
    lines.append('line')
            .attr("x1", function(d) { return x(d,name_u); })
            .attr("x2", function(d) { return x(d,name_u); })
            .attr("y1", hist_chart_height)
            .attr("y2", 0)
            .attr("stroke-width", 2)
            .attr("stroke", "red")
            .style("stroke-dasharray", "4,4");
}



function bar_chart(data,hist_chart_width, hist_chart_height, chart_margin, id) {


    var x = d3.scaleBand()
        .rangeRound([0, hist_chart_width])
        .paddingInner(0.1)
        .domain(data.map(function(d) { return d.label; }));

    var y = d3.scaleLinear()
        .range([hist_chart_height, 0])
        .domain([0, 100]);


    var xAxis = d3.axisBottom(x);

    var yAxis = d3.axisLeft(y);



    var svg = d3.select(id)
        .attr("width", hist_chart_width)
        .attr("height", hist_chart_height)
        .append("g")
        .attr('id', 'inner_graph')
        .attr("transform", "translate(" + chart_margin.left + "," + chart_margin.top + ")");


    var tip = d3.tip()
      .attr('class', 'd3-tip-small')
      .html(function(d) { 
          return "<p> Mean: " + d.labtip + "</p>"
           });

    svg.call(tip);

    svg.selectAll("bar")
        .data(data)
        .enter()
        .append("rect")
        .attr("class", "hist_bar_small")
        .attr("x", function(d) { return x(d.label); })
        .attr("y", function(d) { return y(d.value); })
        .attr("width", x.bandwidth())
        .attr("height", function(d) { return (hist_chart_height - y(d.value)); })
        .on('mouseover', tip.show)
        .on('mouseout', tip.hide);

    console.log(svg)

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + hist_chart_height + ")")
        .call(xAxis)
    
    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis);


    svg.append("text")
        .attr("id", "ylabel")   
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - chart_margin.left)
        .attr("x",0 - (hist_chart_height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text("% ever smoked"); 



}



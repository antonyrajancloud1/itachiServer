$(document).on("click","#webhookStatus",function(){
    var webhookStatus = $("#webhookStatus").prop("checked");
    var nameMap = {"true":"Enabled","false":"Disabled"};
        $.get("/settoggle/"+webhookStatus);

});
$(document).on("click",function(event){
    var idOfTarget = event.target.id;
    if(idOfTarget == "CE" || idOfTarget == "PE"|| idOfTarget == "exitOrder" || idOfTarget == "BN_CE"|| idOfTarget == "BN_PE"|| idOfTarget == "BN_exitOrder"){
        var httpMap = {"CE":"/buy",    "PE":"/sell",    "exitOrder":"/exit_nifty",    "BN_CE":"/buy_bank_ce",    "BN_PE":"/buy_bank_pe",    "BN_exitOrder":"/exit_bank_nifty"};
        $.get(httpMap[idOfTarget],function(data,status){
            if(status=="success"){
                getValues();
            }
        });
    }
});
function getValues(){
 $.get("/getvalues", function(data){
               var order="";
               if(data.currentPremiumPlaced=="") {
                    order="No orders yet!";
               }else{
                     order=data.currentPremiumPlaced;
               }
               var bn_order="";
               if(data.currentPremiumPlaced=="") {
                    bn_order="No orders yet!";
               }else{
                     bn_order=data.currentPremiumPlacedBN;
               }
               document.getElementById("order").innerHTML = order ;
               document.getElementById("lots").innerHTML = data.lots;
               document.getElementById("target").innerHTML = data.targetPoints;
               document.getElementById("account").innerHTML = data.userName;
                document.getElementById("BNorder").innerHTML = bn_order;
                 document.getElementById("BNlots").innerHTML = data.bn_lots;
                  document.getElementById("BNtarget").innerHTML = data.bn_targetPoints;

    });
 }

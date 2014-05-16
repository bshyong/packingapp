def status(gender, type, gen_user, beach, hiking, festival, work, cold, rainy, weather):
    status = "na"
    if gender=="N" or gen_user==gender:
        if any([type=="Beach" and beach=="on", 
            type=="Hiking" and hiking=="on", 
            type=="Festival" and festival=="on",
            type=="Work" and work=="on", 
            type=="All"]): 
            if any([weather=="All",
                weather=="Cold" and cold=="on",
                weather=="Rainy" and rainy=="on",
                weather=="Warm" and warm=="on"]):
                status = "not packed"
    return status
		

def quant(item, days, cold, warm, rainy, type_packer, freq):
    quant = ""
    if freq == "Multiple":
        if type_packer=="heavy":
            quant= str(min(days,14)+2)
        elif type_packer=="light":
            quant= str(min(days,7)+1)
        else:
            quant= str(min(days,10)+2)
    elif freq == "Moderate":
        if type_packer=="heavy":
            if item=="Sweater" and cold=="on":
                quant= str(min(days,5))
            elif item=="Sweater" and cold=="":
                quant= str(1)
            else:
                quant= str(min(days,10))
        elif type_packer=="light":
            if item=="Sweater" and cold=="on":
                quant= str(min(days,4))
            elif item=="Sweater" and cold=="":
                quant= str(1)
            else:
                quant= str(min(days,5))
        else:
            if item=="Sweater" and cold=="on":
                quant = str(min(days,5))
            elif item=="Sweater" and cold=="":
                quant=str(1)
            else:
                quant= str(min(days,7))
    else:
        pass
    return quant

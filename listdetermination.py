def det(item, category, gender, freq, type, packed, packed_side, gen_user, days, beach, hiking, 
	festival, work, cold, rainy, type_packer, current_category):
	code=""
	itemname=""
	if category == current_category and packed==packed_side:
		if gender=="N" or gen_user==gender:
			if any([type=="Beach" and beach=="on", 
				type=="Hiking" and hiking=="on", 
				type=="Festival" and festival=="on",
				type=="Work" and work=="on", 
				type=="All"]): #does this work?
				if freq == "Single" or all([freq == "Cold",cold=="on"]) or all([freq == "Rainy", rainy=="on"]):
					code = item
				elif freq == "Multiple":
					if type_packer=="Heavy":
						code= str(min(days,14)+2) + " " + item
					elif type_packer=="Light":
						code= str(min(days,7)+1) + " " + item
					else:
						code= str(min(days,10)+2) + " " + item
				elif freq == "Moderate":
					if type_packer=="Heavy":
						if item=="Sweater" and cold=="on":
							code= str(min(days,5))+" " + item
						elif item=="Sweater" and cold=="":
							code= str(1)+" "+ item
						else:
							code= str(min(days,10)) + " " + item
					elif type_packer=="Light":
						if item=="Sweater" and cold=="on":
							code= str(min(days,4))+" " + item
						elif item=="Sweater" and cold=="":
							code= str(1)+" "+ item
						else:
							code= str(min(days,5))+ " " + item
					else:
						if item=="Sweater" and cold=="on":
							code= str(min(days,3))+" " + item
						elif cold=="":
							code= str(1)+" "+ item
						else:
							code= str(min(days,7))+ " " + item
				else:
					return
			else:
				return
		else:
			return
	else:
		return
	print "<div> <input type = 'checkbox' name={{"+item.item+"}}> {{"+code+")}} </div>"
	return




		


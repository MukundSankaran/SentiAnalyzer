#This program reads FourSquare user reviews from a set of JSON files and analyzes their sentiment 

import json
import os
import re
import urllib
import libxml2dom
import enchant #We use the PyEnchant spellchecker to correct spellings
import string

#Set the language for the spellchecker as English
d = enchant.Dict("en_US")

#These are inputs used by the program
SWfile = open('/home/Sentiment/SW.txt')
Emofile = open('/home/Sentiment/Emoticons.txt')
Negfile = open('/home/Sentiment/Negatives.txt')

#Flag variable to check if WordNet returns a hit for a synonym
wnflag=0

#Used while printing results - Keeps track of tips
counter = 0
inst = 0

#Calls the Dictionary of Affect in Language(DAL) web service with a word to determine its valence and activation scores
def getMeasure(w):
		
   f = urllib.urlopen("http://compling.org/cgi-bin/DAL_sentence_xml.cgi?sentence="+w)
   s = f.read()
   f.close()
   
   #Parse the XML result to obtain valence and activation scores
   doc = libxml2dom.parseString(s)
   measure = doc.getElementsByTagName("measure")
   valence = measure[0].getAttribute("valence")        
   activation = measure[0].getAttribute("activation")   

   return [valence,activation]

#Check WordNet for Synonyms
def checkWordNet(type)
      TypeList = [];
	if os.path.getsize("/home/Sentiment/"+type+".txt") > 0:
		inFile = open('/home/Sentiment/'+type+'.txt')
		for line in inFile:
			for word in line.split():
                  	if word == "Sense":
                        	wnflag=1
                        	continue 
                        if wnflag != 1:
                        	continue
                        Type.append(word)
                 	wnflag=0
			for w in TypeList:
				t=re.sub("[\,\>\=\'0-9 ]*", "",w)
				#Find if this synonym is available on DAL	
			      if t != "" or t != "Sense":
                        	try: 
                        		r = getMeasure()
                                    valence = r[0]
                                    activation = r[1]
                             	except:
                                    continue 
                        if valence != "":
                        	break  
			del TypeList[0:len(TypeList)]
			inFile.close()

	return [valence,activation]

#Path to the JSON files containing the tips (user reviews)
path='/home/Sentiment/Tips'
files=os.listdir(path)

#Loop through each file and calculate the sentiment of all reviews
for f in files:

      #These variables track the level of positive/negative words in the review. Eg: Highly positive = highP , Low positive = lowP etc
      highP=lowP=highN=lowN=0
	inf=1

      #Flag to indicate that the word is a negative qualifier eg: not, don't, won't etc
      Nflag=0

      #Flags to show that word is in CAPS, has exclamation marks, is a stop word etc
      sflag=exc=caps=0 
      
      #Open the tips JSON file
	json_data=open('/home/Sentiment/Tips/'+f)          
      
      #Corrupt JSON file. Load next file          
      try: 
	  data = json.load(json_data)
      except:
        continue
      
      #Navigate JSON structure to obtain the tips (reviews)
	L = data["response"]["tips"]["items"]	
	
      #Construct lists from the Emoticons, Stop Words and Negatives files
	Emo = [line.rstrip('\n') for line in Emofile.readlines()]
	SW = [line.rstrip('\n') for line in SWfile.readlines()]
	Neg = [line.rstrip('\n') for line in Negfile.readlines()]
	
      #This will hold all useful words (non stop words) in the tip 
	Sentence = []

	#Loop for all tips left by the user
	for i in L:

            #Individual tip from collection of tips left by a user 
      	Tip = re.sub("[\.\,\!0-9]*", "",i["text"])            
            
            #Words in tip  
		Words = Tip.split()

            #Loop through the words and calculate sentiment of each word
		for j in Words:
                  #Exclamation mark is present in the word - Must mean some sort of excitement. Could be negative/positive.
      		if j.endswith('!'):
           			exc = 1 
                  
                  #Calculates the emotion of the emoticons present in the tip. The list is arranged such that positive emoticons appear first, followed by negative emoticons
        		if j in Emo: 
             		position = Emo.index(j)
             		if position < 38:
                			lowP+=1    
             		elif position < 68:
                  		highP+=1 
             		elif position < 91:
                  		lowN+=1 
             		else: 
                  		highN+=1   

            #Removes all noisy characters                
        	t=re.sub("[\.\,\)\(\:\;\#\-\>\<\^\=\'0-9!\*\]\[\{\}\?\"\$\@\%\&]*", "",j)
 
            #Replaces words like Coooool with Cool       
        	m=re.sub(r'(.)\1{3,}',r'\1\1\1',t)    

            #If word is a Stop Word, go to next word in tip    
        	if m.upper() in SW:
	     		continue  

            #Append all useful words (non stop words) to a list
        	Sentence.append(m)        

            #Calculate sentiment scores for each word  
   		for w in Sentence:

                  #If word is in caps - There is some stress               
        		if w.isupper():
          			caps = 1  

                  #If word is a negative word, check the next word. If the next word is positive, sentiment is negative and vice versa
        		if w in Neg:
           			Nflag = 1 

			#Words could become empty after removal of noisy characters
        		if w == "":
            		continue 
                  
                  #Calculate sentiment score for the word from DAL
			try: 
   	            	r = getMeasure()
                        valence = r[0]
                        activation = r[1]  		  
                  except:
                        continue      
                  
			if inf == 1: 
                        #If DAL doesn't return any result i.e it doesn't contain the word, substitute with a synonym and check again. Synonyms are obtained using WordNet  
				if valence == "":
			             os.system("/usr/local/WordNet-3.0/bin/wn "+w+" -synsn > noun.txt")
			             os.system("/usr/local/WordNet-3.0/bin/wn "+w+" -synsv > verb.txt")
			             os.system("/usr/local/WordNet-3.0/bin/wn "+w+" -synsa > adj.txt")
			             os.system("/usr/local/WordNet-3.0/bin/wn "+w+" -synsr > adv.txt")

					#Check Noun synonyms
			      	res = checkWordNet("noun")
                              valence = res[0] 
					activation = res[1]
  				
				#If no noun synonym is found, check for verb synonyms	
	 		      if valence == "":
					res = checkWordNet("verb")
					valence = res[0] 
					activation = res[1]

				#Check adjective synonyms next		
             		if valence == "":
                			res = checkWordNet("adj")
					valence = res[0] 
					activation = res[1]
	             			     
                        #Check adverbs next
				if valence == "":
			            res = checkWordNet("adv")
    					valence = res[0] 
					activation = res[1]      
	                                                           
			valence=float(valence)
        		activation=float(activation)

                  #Sum up scores based on all the flags raised and valence, activation values
			if valence <= 1.5:
             		if Nflag == 1:
			      	if activation < 2.0:               
			            	lowP+=1
		                  	if sflag == 1: 
                     				lowP+=0.5
		                  	if exc == 1:
                     				lowP+=0.5
		                  	if caps == 1:
                     				lowP+=0.25  
                 			else: 
                    			highP+=1
                    			if sflag == 1: 
                       				highP+=0.5 
                    			if exc == 1:
                       				highP+=0.5
                    			if caps == 1:
                       				highP+=0.25
                 			      Nflag = 0       
             		if activation < 2.0:                
                    		highN+=1 
                    		if sflag == 1 or exc == 1:
                       			highN+=0.5
                    		if caps == 1:
                       			highN+=0.25
             		else: 
                    		lowN+=1
                    		if sflag == 1 or exc == 1:
				            lowN+=0.5
                    		if caps == 1:
                       			lowN+=0.25                                                                                      
        		elif valence >= 2.25:
               		if Nflag == 1:
                  		if activation < 2.0:                
                    			highN+=1
                    			if sflag == 1 or exc == 1:
                       				highN+=0.5
                    			if caps == 1:
                       				highN+=0.25  
                  		else: 
                    			lowN+=1
                    			if sflag == 1 or exc == 1:
                       				lowN+=0.5
                    			if caps == 1:
                       				lowN+=0.25
                  		Nflag = 0
               		if activation < 2.0:
                    		lowP+=1
                    		if sflag == 1:
                       			lowP+=0.5
                    		if exc == 1:
                       			lowP+=0.5  
                    		if caps == 1:
                       			lowP+=0.25   
               		else: 
                    		highP+=1
                    		if sflag == 1:
                       			highP+=0.5
                    		if exc == 1:
                       			highP+=0.5
                    		if caps == 1:
                       			highP+=0.25
         
			#Print Results	
                	counter+=1
                	print(counter)        
                	if highP == 0 and lowP == 0 and highN == 0 and lowN == 0:
                 		print('<--Tip--> '+Tip)  
                        print('<--Pol--> This review is Neutral')
                  
                	elif (highP + lowP) > (highN + lowN):
                        print('<--Tip--> '+Tip)
                        print('<--Pol--> This review is positive')  
                        
                	elif (highP + lowP) < (highN + lowN):
                        print('<--Tip--> '+Tip)   
                        print('<--Pol--> This review is negative')
                        
                	else:
                  	if highP > highN:
                        	print('<--Tip--> '+Tip)
                        	print('<--Pol--> This review is positive')
                                 
                   	elif highP < highN:
                        	print('<--Tip--> '+Tip)
                        	print('<--Pol--> This review is negative')
                        
                   	else:
                      		if lowP > lowN:
                        	print('<--Tip--> '+Tip)
                        	print('<--Pol--> This review is positive')  
                        
                      	elif lowP < lowN:
                        	print('<--Tip--> '+Tip)
                        	print('<--Pol--> This review is Negative') 
                          
                      	else:
                        	print('<--Tip--> '+Tip)
                        	print('<--Pol--> Could not resolve polarity') 
                        
		highP = lowP = highN = lowN = caps = sflag = exc = 0   
		del Sentence[0:len(Sentence)]                  
      json_data.close()

#Close all opened files
SWfile.close()
Emofile.close()
Negfile.close()
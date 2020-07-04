import sys
import traceback
import getopt
import os.path
import json
import datetime
import pprint
#from collections.abc import Mapping
import collections.abc

from progress.spinner import Spinner

keys_used = {}
extra_keys = {}
states_processed = []


def main(argv):
    inputfile = ''
    inputdir = ''
    outputpath = ''
    try:
        opts, args = getopt.getopt(argv, "hi:o:d:", ["ifile=","opath=","idir="])
    except getopt.GetopError:
        print ('USAGE python cve4to5up.py -i <inputfile>|-d <inputdirectory> -o <outputpath>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-d", "--idir"):
            inputdir = arg
        elif opt in ("-o", "--opath"):
            outputpath = arg
    if inputfile and outputpath:
        CVE_Convert(inputfile, outputpath)
    elif inputdir and outputpath:
        # loop all *.JSON in input directory
        print('START processing directory: ', inputdir)
        spinner = Spinner('Converting ')
        problemfiles = {}
        CVECount = 0
        for subdir, dirs, files in os.walk(inputdir):
            for file in files:
                filepath = subdir + os.sep + file
                opath = ''
                if filepath.lower().endswith(".json"):
                    # strip input path from subdir
                    dtree = subdir
                    if dtree.startswith(inputdir):
                        dtree = dtree.replace( inputdir, '')
                    opath = outputpath + dtree
                    try:
                        CVE_Convert(filepath, opath)    
                    except:
                        problemfiles[filepath] = "" + str(sys.exc_info()[0]) + " -- " + str(sys.exc_info()[1]) + " -- "
                CVECount += 1    
                if CVECount % 250 == 0: spinner.next()
        
        # insert blank lines to clear spinner    
        print('FINISHED processed directory', inputdir)
        print('')
        print('PROBLEM FILE REPORT')
        if problemfiles:
            print("JSON files that failed to convert: ")
            for fname in problemfiles:
                print(fname)
                print("    ", problemfiles[fname])
        else:
            print("All JSON files converted.")
        print('')
        
        print("Extra keys encountered")
        if extra_keys:
            for e in extra_keys:                
                print( e )
                for ek in extra_keys[e]:
                    print("    ", ek)
        else:
            print('No extra keys found. Keys seen:')
            for e in keys_used:
                print( e )
                for edk in keys_used[e]:
                    print("    ", edk)
                
        print('')
        print('Saw STATEs')
        for s in states_processed:
            print(s)
            
        print('')
        if extra_keys:
            print('')
            print("Detailed Extra keys encountered")
            for e in extra_keys:                
                print( e )
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(extra_keys[e])
            print('')
            print('')
            print('')

        print('Done')


        
    else:
        print('incorrect input parameters')
        print ('USAGE python cve4to5up.py -i <inputfile>|-d <inputdirectory> -o <outputpath>')    
        
    sys.exit(0)
            
            
            
def CVE_Convert(inputfile, outputpath):  
    # print("input - ", inputfile, " :: output - ", outputpath)
    global keys_used
    global extra_keys
    global states_processed
    
    with open(inputfile) as json_file:
        writeout = False
        data = json.load(json_file)
        jout = {}
        jout["data_format"] = "MITRE"
        keys_used["data_format"] = {}
        jout["data_type"] = "CVE"
        keys_used["data_type"] = {}
        jout["data_version"] = "5.0"
        keys_used["data_version"] = {}
        
        # up convert meta
        o_meta = {}
        try:
            if "CVE_data_meta" in data and "STATE" in data["CVE_data_meta"]:
                i_meta = data["CVE_data_meta"]
                if "ASSIGNER" in i_meta: 
                    o_meta["ASSIGNER"] = i_meta["ASSIGNER"]

                if "STATE" in i_meta: 
                    o_meta["STATE"] = i_meta["STATE"]
                    if o_meta["STATE"] not in states_processed: states_processed.append(o_meta["STATE"])

                if "ID" in i_meta: 
                    o_meta["ID"] = i_meta["ID"]

                if "DATE_PUBLIC" in i_meta: 
                    o_meta["DATE_PUBLIC"] = i_meta["DATE_PUBLIC"]

                if "TITLE" in i_meta: 
                    o_meta["TITLE"] = i_meta["TITLE"]
                    
                if i_meta["STATE"] not in keys_used: keys_used[i_meta["STATE"]] = {}
                keys_used[i_meta["STATE"]]["CVE_data_meta"] = {}
                keys_used[i_meta["STATE"]]["data_format"] = {}
                keys_used[i_meta["STATE"]]["data_type"] = {}
                keys_used[i_meta["STATE"]]["data_version"] = {}
            else:
                raise MissingRequiredPropertyValue(inputfile, "CVE_data_meta no STATE")
        except Exception as e:
            if type(e) is not MissingRequiredPropertyValue:
                raise MissingRequiredPropertyValue(inputfile, "CVE_data_meta structure error")
            else:
                raise
            
        o_meta["UPDATED"] = datetime.date.today().strftime("%Y-%m-%d")    
        jout["CVE_data_meta"] = o_meta

        # public up convert
        if o_meta["STATE"].upper() == "PUBLIC":
            o_cna = {}    
            if "description" in data and "description_data" in data["description"]:
                keys_used["PUBLIC"]["description"] = ""
                o_cna["descriptions"] = []
                for i_desc in data["description"]["description_data"]:
                    o_desc = {}
                    if "lang" in i_desc: o_desc["lang"] = i_desc["lang"]
                    if "value" in i_desc: o_desc["value"] = i_desc["value"]
                    o_cna["descriptions"].append(o_desc)

            if "affects" in data:
                keys_used["PUBLIC"]["affects"] = ""
                o_cna["affected"] = {}
                i_affects = data["affects"]
                o_affected = {}
                #vendors
                if "vendor" in i_affects:
                    vendors = []
                    for i_vd in i_affects["vendor"]["vendor_data"]:
                        vendor = {}
                        vendor["vendor_name"] = i_vd["vendor_name"]
                        if "product" in i_vd and "product_data" in i_vd["product"]:
                            products = []
                            for vd_pd in i_vd["product"]["product_data"]:
                                product = {}
                                if "vendor_name" in vd_pd: product["product_name"] = vd_pd["product_name"]
                                if "version" in vd_pd and "version_data" in vd_pd["version"]:
                                    vers = []
                                    for pd_vd in vd_pd["version"]["version_data"]:
                                        ver = {}
                                        if "version_value" in pd_vd: ver["version_value"] = pd_vd["version_value"]
                                        if "version_affect" in pd_vd: ver["version_affected"] = pd_vd["version_affect"]
                                        vers.append(ver)
                                    product["versions"] = vers
                                products.append(product)
                            vendor["products"] = products
                        vendors.append(vendor)   
                    o_affected["vendors"] = vendors
                    
                # CPE

                # SWID

                o_cna["affected"] = o_affected
            # done with affected up convert
            
            if "references" in data and "reference_data" in data["references"]:
                keys_used["PUBLIC"]["references"] = ""
                o_cna["references"] = []
                for i_ref in data["references"]["reference_data"]:
                    o_ref = {}
                    if "name" in i_ref: o_ref["name"] = i_ref["name"]
                    if "refsource" in i_ref: o_ref["refsource"] = i_ref["refsource"]
                    if "url" in i_ref: o_ref["url"] = i_ref["url"]
                    o_cna["references"].append(o_ref)
                 
            # end of reference up convert    

            if "credit" in data:
                keys_used["PUBLIC"]["credit"] = ""
                o_cna["credits"] = []
                for i_credit in data["credit"]:
                    if "lang" in i_credit and "value" in i_credit:
                        o_credit = {}
                        o_credit["lang"] = i_credit["lang"]
                        o_credit["value"] = i_credit["value"]
                        o_cna["credits"].append(o_credit)
                        
            if "impact" in data and data["impact"] and not(data["impact"] is None): # impact is an unofficial community added property under CVE 4.0 that maps to metrics array in CVE 5
                keys_used["PUBLIC"]["impact"] = ""
                try:
                    o_cna["metrics"] = []
                    for i_impact in data["impact"]:
                        # print("ID = ", o_meta["ID"])
                        # pp = pprint.PrettyPrinter(indent=4)
                        # pp.pprint(i_impact)
                        o_impact = {}
                        
                        iver = "other"
                        iobj = {}
                        if isinstance(data["impact"], collections.abc.Mapping):
                            if i_impact == "cvss" and "version" in data["impact"][i_impact]:                            
                                if data["impact"][i_impact]["version"] == "3.1":
                                    iver = "cvss-v_3_1"
                                elif data["impact"][i_impact]["version"] == "3.0":
                                    iver = "cvss-v_3_0"
                                elif data["impact"][i_impact]["version"] == "2.0":
                                    iver = "cvss-v_2_0"                            
                                else:
                                    pass
                                iobj = data["impact"][i_impact]
                            elif i_impact == "cvssv3":
                                iver = "cvss-v_3_0"
                                iobj = data["impact"][i_impact]
                            elif i_impact == "cvss" and isinstance(data["impact"][i_impact], list):
                                for tc in data["impact"][i_impact]: # array of arrays
                                    if ( isinstance(tc, list) ): # list in list
                                        for ic in tc: # inner array
                                            lver = "other"
                                            iver = "skip" #skip the external o_impact because we found an array instead of a object                                            
                                            if "version" in ic:
                                                if ic["version"] == "3.1":
                                                    lver = "cvss-v_3_1"
                                                elif ic["version"] == "3.0":
                                                    lver = "cvss-v_3_0"
                                                elif ic["version"] == "2.0":
                                                    lver = "cvss-v_2_0"
                                                else:
                                                    print()
                                                    print("ID = ", o_meta["ID"])
                                                    print('UNEXPECTED IMPACT (array[array]) VERSION FOUND == ', i_impact)
                                                    print()
                                                    pass                                    
                                            else:
                                                print("didn't find version")
                                                print(ic)
                                                raise MissingRequiredPropertyValue(o_meta["ID"], "IMPACT.version from cvss[[{}]]" )
                                            
                                            if lver == "other":
                                                o_impact[lver] = {}
                                                o_impact[lver]["type"] = "unknown"
                                                o_impact[lver]["content"] = ic
                                            else:
                                                o_impact[lver] = ic 
                                    elif (isinstance(tc, collections.abc.Mapping)): # array of objects
                                            lver = "other"
                                            iver = "skip" #skip the external o_impact because we found an array instead of a object                                            
                                            if "version" in tc:
                                                if tc["version"] == "3.1":
                                                    lver = "cvss-v_3_1"
                                                elif tc["version"] == "3.0":
                                                    lver = "cvss-v_3_0"
                                                elif tc["version"] == "2.0":
                                                    lver = "cvss-v_2_0"
                                                else:
                                                    print()
                                                    print("ID = ", o_meta["ID"])
                                                    print('UNEXPECTED IMPACT (array[objects]) VERSION FOUND == ', i_impact)
                                                    print()
                                                    pass                                    
                                            else:
                                                print("didn't find version")
                                                print(tc)
                                                raise MissingRequiredPropertyValue(o_meta["ID"], "IMPACT.version from cvss[{}]" )
                                            
                                            if lver == "other":
                                                o_impact[lver] = {}
                                                o_impact[lver]["type"] = "unknown"
                                                o_impact[lver]["content"] = tc
                                            else:
                                                o_impact[lver] = tc 

                                    else:
                                        raise UnexpectedPropertyValue( o_meta["ID"], "Impact - cvss structure not recognized")
                                        
                            else:
                                print()
                                print("ID = ", o_meta["ID"])
                                print('UNEXPECTED IMPACT(property) VERSION FOUND == ', i_impact)
                                print()
                                    
                            if iver == "other":
                                o_impact[iver] = {}
                                o_impact[iver]["type"] = "unknown"
                                o_impact[iver]["content"] = data["impact"][i_impact]
                            elif iver == "skip":
                                pass
                            else:
                                o_impact[iver] = data["impact"][i_impact]
                        else:
                            o_impact[iver] = {}
                            o_impact[iver]["type"] = "unknown"
                            o_impact[iver]["content"] = data["impact"]

                        o_cna["metrics"].append(o_impact)
                except Exception as e:
                    raise UnexpectedPropertyValue(o_meta["ID"], "IMPACT", str(e))

            if "problemtype" in data and "problemtype_data" in data["problemtype"]:
                keys_used["PUBLIC"]["problemtype"] = ""
                o_problemtypes = {}          
                i_pds = data["problemtype"]["problemtype_data"]
                for i_pd in i_pds:
                    o_descs = []
                    if "description" in i_pd:
                        for i_desc in i_pd["description"]:                        
                            o_pd = {}
                            o_pd["type"] = "text"
                            for dk in i_desc:
                                if dk == "lang":
                                    o_pd["lang"] = i_desc[dk]
                                elif dk == "value":
                                    o_pd["description"] = i_desc[dk]
                                    if i_desc[dk].startswith("CWE-"):
                                        o_pd["type"] = "CWE"
                                        o_pd["CWE-ID"] = i_desc[dk]
                                else:
                                    o_pd[dk] = i_desc[dk]
                            o_descs.append(o_pd)                
                    if "CWE-ID" in i_pd:
                        o_pd = {}
                        o_pd["CWE-ID"] = i_pd["CWE-ID"]
                        o_pd["description"] = i_pd["CWE-ID"]
                        o_pd["lang"] = "eng"
                        o_pd["type"] = "CWE"
                        o_descs.append(o_pd)                
                    
                    if "descriptions" not in o_problemtypes: o_problemtypes["descriptions"] = []
                    o_problemtypes["descriptions"].append(o_descs)
                o_cna["problemtypes"] = o_problemtypes

            if "generator" in data: #community field
                keys_used["PUBLIC"]["generator"] = ""
                try:
                    o_cna["generator"] = data["generator"]
                except:
                    raise UnexpectedPropertyValue(o_meta["ID"], "generator", "JSON not convertable")

            if "source" in data: #community field
                keys_used["PUBLIC"]["source"] = ""
                try:
                    o_cna["source"] = data["source"]
                except:
                    raise UnexpectedPropertyValue(o_meta["ID"], "source", "JSON not convertable")

            if "configuration" in data:
                keys_used["PUBLIC"]["configuration"] = ""
                try:
                    o_cna["configuration"] = data["configuration"]
                except:
                    raise UnexpectedPropertyValue(o_meta["ID"], "configuration", "JSON not convertable")

            if "work_around" in data:
                keys_used["PUBLIC"]["work_around"] = ""
                try:
                    o_cna["work_around"] = data["work_around"]
                except:
                    raise UnexpectedPropertyValue(o_meta["ID"], "work_around", "JSON not convertable")

            if "exploit" in data:
                keys_used["PUBLIC"]["exploit"] = ""
                try:
                    o_cna["exploit"] = data["exploit"]
                except:
                    raise UnexpectedPropertyValue(o_meta["ID"], "exploit", "JSON not convertable")

            if "solution" in data:
                keys_used["PUBLIC"]["solution"] = ""
                try:
                    o_cna["solution"] = data["solution"]
                except:
                    raise UnexpectedPropertyValue(o_meta["ID"], "source", "JSON not convertable")

            # add extra / non-standard content to CNA container to avoid data loss.
            for i_key in data:
                if o_meta["STATE"] in keys_used and i_key not in keys_used[o_meta["STATE"]]:
                    o_cna[i_key] = data[i_key]
                    # o_cna["atest"] = {"test":"success"}

            jout["cna-container"] = o_cna
            writeout = True
            
        elif o_meta["STATE"].upper() == "RESERVED":
            if "description" in data and "description_data" in data["description"]:
                o_meta["descriptions"] = []
                keys_used["RESERVED"]["description"] = ""
                for i_desc in data["description"]["description_data"]:
                    o_desc = {}
                    if "lang" in i_desc: o_desc["lang"] = i_desc["lang"]
                    if "value" in i_desc: o_desc["value"] = i_desc["value"]
                    o_meta["descriptions"].append(o_desc)
            writeout = True
            pass
        elif o_meta["STATE"].upper() == "REJECT":
            if "description" in data and "description_data" in data["description"]:
                o_meta["descriptions"] = []
                keys_used["REJECT"]["description"] = ""
                for i_desc in data["description"]["description_data"]:
                    o_desc = {}
                    if "lang" in i_desc: o_desc["lang"] = i_desc["lang"]
                    if "value" in i_desc: o_desc["value"] = i_desc["value"]
                    o_meta["descriptions"].append(o_desc)
            writeout = True
            pass
        else:
            writeout = False
            raise UnexpectedPropertyValue("STATE", o_meta["STATE"])

        if writeout:
            # write result to file of CVE ID
            fname = os.path.join( outputpath, jout["CVE_data_meta"]["ID"] + ".json")
            os.makedirs(outputpath, exist_ok=True)
            jout_file = open(fname, "w")
            jout_file.write( json.dumps(jout, sort_keys=True, indent=4) )
            jout_file.close

        for i_key in data:
            if i_key in keys_used[o_meta["STATE"]]:
                #root key was converted
                pass
            else:
                #found a key that was not explicitly converted
                #these CVEs should be reviewed for validity.
                if o_meta["STATE"] not in extra_keys: extra_keys[o_meta["STATE"]] = {}
                if i_key not in extra_keys[o_meta["STATE"]]: extra_keys[o_meta["STATE"]][i_key] = []
                if o_meta["ID"] not in extra_keys[o_meta["STATE"]][i_key]: extra_keys[o_meta["STATE"]][i_key].append(o_meta["ID"])
                                

class UnexpectedPropertyValue(Exception):
    def __init__(self, cveid, propertyname, message="unexpected value in property"):
        self.propertyname = propertyname
        self.cveid = cveid
        self.message = message
        super().__init__(self.message)
    def __str__(self):
        return self.cveid + " - " + self.propertyname + " - " + self.message 

class MissingRequiredPropertyValue(Exception):
    def __init__(self, cveid, propertyname, message="Required property missing from CVE"):
        self.propertyname = propertyname
        self.cveid = cveid
        self.message = message
        super().__init__(self.message)
    def __str__(self):
        return self.cveid + " - " + self.propertyname + " - " + self.message 

if __name__ == "__main__":
   main(sys.argv[1:])
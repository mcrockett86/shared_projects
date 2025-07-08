import pytesseract
from PIL import Image
from copy import deepcopy
import numpy as np
import pandas as pd
import textdistance

import os


def create_job_titles():
    job_titles = []

    # pre-populate all the text to sort out
    img_files = [x for x in os.listdir('images') if '.DS_Store' not in x and 'titles' not in x]
    img_files.sort()

    #orig_color = (139,144,150)  # gray text
    replacement_color = (0, 0, 0)  # black
    replacement_color_background = (255, 255, 255)  # white


    for i, fi in enumerate(img_files):
        #print(f"create_job_titles: {i}")

        img_path = os.path.join('images/', fi)
        #img_path_out = img_path.replace('.jpeg', '_job_titles.jpeg')

        img_in = Image.open(img_path).convert('RGBA')

        data = np.array(img_in)
        red, green, blue, alpha = data.T # Temporarily unpack the bands for readability

        gray_areas = ( np.logical_and(red>=130, red<=149) & np.logical_and(green>=135, green<=154) & np.logical_and(blue>=140, blue<=160) )

        other_areas = ~gray_areas

        data[..., :-1][gray_areas.T] = replacement_color              # replace gray with black
        data[..., :-1][other_areas.T] = replacement_color_background  # replace other areas with white

        img_out = Image.fromarray(data).convert('RGB')
        #img_out.save(img_path_out)

        # scrape out job titles and add to the list
        try:
            job_titles_text = pytesseract.image_to_string(img_out)
            job_titles_clean = [x for x in job_titles_text.split('\n') if x != '' and len(x) > 1]
            print(f"img_{i}; job_titles_clean: {job_titles_clean}")
            job_titles += job_titles_clean
        except:
            pass

    return job_titles


job_titles = create_job_titles()


def clean_small_text(text):

    # strip any chars that are less than or equal to length of 2
    text_list = text.split(" ")
    text_clean = " ".join([x for x in text_list if len(x)>2])

    return text_clean


def is_human_name(text):

    # split text up and remove any strings less than minimum length

    # length of resulting list should be 2 to 3 

    pass


# detect a company name vs. a person name
# implemented 
def is_company_name(input_str):
    if '>' in input_str:
        idx_of_char = input_str.index('>')
        return (True, input_str[0:idx_of_char].rstrip(' '))
    
    else:
        return (False, None)


def is_job_title(input_str):
    for job_title in job_titles:

        # this does fuzzy matching for two strings being close to each other
        similarity_score = textdistance.levenshtein.normalized_similarity(job_title, input_str)

        # escape if close enough match found
        if similarity_score > 0.50:
            return True
    
    # default case false
    return False


# implemented
def is_clock(input_str):

    pass

# implemented
def is_header(input_str):
    if 'Organizations & Att' in input_str:
        return True
    
    elif ':' in input_str:
        return True
    
    else:
        return False

text_list = []

# pre-populate all the text to sort out
img_files = [x for x in os.listdir('images') if '.DS_Store' not in x and '_titles' not in x]
img_files.sort()

for i, fi in enumerate(img_files):
    #print(f"extracting total image texts: {i}")
    img_path = os.path.join('images/', fi)

    # TODO: may not want to split since the company name has multiple lines sometimes
    img_text = pytesseract.image_to_string(Image.open(img_path))
    img_text_list_cleaned = [x for x in img_text.split('\n') if x != '']
    print(f"img_{i}; img_text_list_cleaned: {img_text_list_cleaned}")

    text_list += img_text_list_cleaned


# this is the cleaned output
dict_companies = {}
current_company = None


for i, val_str in enumerate(text_list):
    try:
        #print(val_str)

        # strip out the clock and header
        if is_header(val_str):
            continue 

        elif is_clock(val_str):
            continue
        
        else:
            (result_bool, company_name_clean) = is_company_name(val_str)
            print(f"company_name_clean: {company_name_clean}")

            if result_bool and (company_name_clean not in dict_companies.keys()):
                dict_companies[company_name_clean] = []
                current_company = company_name_clean
                print(f"created company: {current_company}")
                continue
            
        # now add strings that come after that into the dict list for that company
        dict_companies[current_company].append(val_str)

    except Exception as error:
        print(error)
        #breakpoint()


for key in list(dict_companies.keys()):

    len_results = len(dict_companies[key])

    if len_results == 0:
        #print("removing empty company key")
        del dict_companies[key]

    # clean the text of small names and weird characters
    else:
        list_company_entities = dict_companies[key]
        list_company_entities_clean = []

        for text in list_company_entities:
            clean_text = clean_small_text(text)
            list_company_entities_clean.append(clean_text)

        # replace the existing dict with the cleaned text list
        dict_companies[key] = list_company_entities_clean

#print(dict_companies)

# screen through companies and see list
dict_companies_entities = dict()

for key in list(dict_companies.keys()):
    dict_companies_entities[key] = []

    company_entities = dict_companies[key]
    print(f"company: {key}")
    print(f"company_entities: {company_entities}")

    try:
        bool_list_job_titles_np_arr = np.array([is_job_title(x) for x in company_entities])
        bool_list_person = np.invert(bool_list_job_titles_np_arr).tolist()
    except Exception as error:
        print(error)
        breakpoint()

    current_person_name = None
    current_person_job_title = None

    past_person_name = None

    current_person_dict = {'name': '', 'title': ''}

    # TODO: figure out why not adding the first person
    for i, entity in enumerate(company_entities):

        #if key == 'MS Rau Grits M.S. Rau':
        #    breakpoint()

        is_person = bool_list_person[i]
        is_entity = bool_list_job_titles_np_arr.tolist()[i]

        if is_person:
            person_name = company_entities[i]

            # if new person, create a new person dict and add prior person dict
            if current_person_dict['name'] != person_name:
                prior_person_dict = current_person_dict

                print("adding prior_person_dict")
                print(prior_person_dict)

                dict_companies_entities[key].append(prior_person_dict)

                current_person_dict = {'name': person_name, 'title': ''}

        elif is_entity:
            current_person_dict['title'] += f" {entity}"
            pass

        else:
            print("something went wrong")

    # add the last name from current_person_dict
    dict_companies_entities[key].append(current_person_dict)


#dict_companies_entities

# put into pandas dataframe
df_out = pd.DataFrame()

for company_name in dict_companies_entities.keys():
    for entity in dict_companies_entities[company_name]:
        #print(entity)

        dict_entity = {
            'company_name': company_name,
            'person_name': entity['name'],
            'person_title': entity['title']
        }


        df_entity = pd.DataFrame([dict_entity])
        df_out = pd.concat([df_out, df_entity], ignore_index=True)


# do some minor cleaning

# remove na rows for column person_name
df_out = df_out[df_out['person_name'] != '']
df_out = df_out[df_out['person_title'] != '']

# drop duplicate people
df_out = df_out.drop_duplicates(subset=['person_name'])

# strip trailing and leading spaces
df_out['company_name'] = df_out['company_name'].str.lstrip(" ").str.rstrip(" ").str.upper()
df_out['person_name'] = df_out['person_name'].str.lstrip(" ").str.rstrip(" ").str.upper()
df_out['person_title'] = df_out['person_title'].str.lstrip(" ").str.rstrip(" ").str.upper()

print(df_out)

df_out.to_csv("images_processed.csv", index=False)
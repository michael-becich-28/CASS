#Import regular expression library and sys for exit()
import re, sys, math, numpy, pylab, ast
import random as rng

#Exception that is raised when an error is found during parsing
class ParsingSyntaxError(Exception):
    def __init__(self, string):
        #Print error message
        print string
        print
        print "The program will now exit."
        sys.exit(1)

#Some working test strings
testStrings = ["12air + glucose -> 6water + 6co2 [.01]","air + 2h2 -> 2water [.005]","2water + 3sucrose -> air + co2 [.03]","sucrose + co2 -> glucose [.01]","water = 1.23e+10","air = 1.23e+10","glucose = 1.23e+10","h2 = 1.23e+10","co2 = 10000","sucrose = 2.5e+8"]

def notAllMatched(inputString, matches):
    found = [False]*len(inputString)
    allFound = []
    for match in matches:
        for i in range(match.start(), match.end()):
            found[i] = True
    i = 0
    while i < len(found):
        characterThere = found[i]
        if not characterThere:
            startPos = i
            while (not characterThere) and (i < len(found)):
                characterThere = found[i]
                i+=1
            endPos = i
            errorString = inputString[startPos:endPos]
            allFound.append([startPos, endPos, errorString])
        i+=1
    return allFound           
    
#Text parsing function
def parseText(inputStrings):
    #Define lists and dictionaries we want to return
    moleCounts = {}
    equations = []
    
    #Regular expressions
    regExpEqPlus = """
    \s*                             #Find leading whitespaces
    (\d*)                           #Find integers
    \s*                             #Ignore whitespaces
    ([^\s\+>\-\[]+)                 #Read characters as word until non-internal digit, whitespace or symbol (+,-,=,>)
    \s*                             #Ignore whitespaces
    \+                              #Find +
    \s*                             #Find trailing whitespaces
    """
    regExpEqArrow = """
    \s*                             #Find leading whitespaces
    (\d*)                           #Find integers
    \s*                             #Ignore whitespaces
    ([^\s\+>\-\[]+)                 #Read characters as word until non-internal digit, whitespace or symbol ([,+,-,=,>)
    \s*                             #Ignore whitespaces
    \->                             #Find arrow
    \s*                             #Find trailing whitespaces
    """
    regExpEqEnd = """
    \s*                             #Find leading whitespaces
    (\d*)                           #Find integers
    \s*                             #Ignore whitespaces
    ([^\s\+>\-\[]+)                 #Read characters as word until space or open bracket
    \s*                             #Ignore whitespaces
    \[                              #Find open bracket
    \s*                             #Find trailing whitespaces
    """
    regExpEqConstant = """
    \s*                             #Find leading whitespaces
    \[                              #Find open brackets
    \s*                             #Ignore whitespaces
    ([\d\.\-]*)                     #Find numbers
    \s*                             #Ignore whitespaces
    \]                              #Find close brackets
    \s*                             #Find trailing whitespaces
    """
    regExpDeclaration = """
    \s*                             #Find leading whitespaces
    ([^\s\+>\-]+)                   #Read characters as word until non-internal digit, whitespace or symbol (+,-,=,>)
    \s*                             #Ignore whitespaces
    =                               #Find equal sign
    \s*                             #Ignore whitespaces
    ([^\s]+)                      #Find integers 
    \s*                             #Find trailing whitespaces
    """
    
    for i, line in enumerate(inputStrings):
        #Define outputs
        reactants = {}
        products = {}
        netChange = {}
        moleCount = 0
        constant = 0
        
        #Put all regex matches in a list
        eqPlusMatches = list(re.finditer(regExpEqPlus, line, re.VERBOSE))
        eqArrowMatches = list(re.finditer(regExpEqArrow, line, re.VERBOSE))
        eqEndMatches = list(re.finditer(regExpEqEnd, line, re.VERBOSE))
        eqConstantMatches = list(re.finditer(regExpEqConstant, line, re.VERBOSE))
        declarationMatches = list(re.finditer(regExpDeclaration, line, re.VERBOSE))

        #for match in eqPlusMatches + eqArrowMatches + eqEndMatches:
        #    print match.groups()
        
        #Check for errors
        if len(eqArrowMatches) > 1:
            raise ParsingSyntaxError("ERROR: The parser found more than one arrow in line " + str(i) + ":\n" + line)        
        if len(eqEndMatches) > 1:
            raise ParsingSyntaxError("ERROR: The parser found more than one equation terminator in line (you may be missing a '+') " + str(i) + ":\n" + line)
        if len(eqConstantMatches) > 1:
            raise ParsingSyntaxError("ERROR: The parser found more than one reaction constant in line " + str(i) + ":\n" + line)
        if (len(eqConstantMatches) < 1 and len(declarationMatches) <1):
            raise ParsingSyntaxError("ERROR: The parser found no reaction constant in line " + str(i) + ":\n" + line)
        if len(declarationMatches) > 1:
            raise ParsingSyntaxError("ERROR: The parser found more than one equal sign in line " + str(i) + ":\n" + line)
        if len(eqArrowMatches) == len(declarationMatches):
            raise ParsingSyntaxError("ERROR: The parser could not determine whether line " + str(i) + " is a molecule-count declaration or reaction equation:\n" + line)
        
        definitionOrEquation = bool(len(declarationMatches))   #If the line is an definition, lineType will be True. If the line is an equation, lineType will be False.
        
        notMatchedData = notAllMatched(line, eqPlusMatches + eqArrowMatches + eqEndMatches + eqConstantMatches + declarationMatches)
        if notMatchedData != None:
            for notMatchedSet in notMatchedData:
                print "WARNING: The parser could not identify the meaning of line " + str(i+1) + " characters ",
                print str(notMatchedSet[0]) + " through " + str(notMatchedSet[1]) + ": " + notMatchedSet[2]
                print "Ignoring error(s)..."
        
        if definitionOrEquation == False:   #If the line is an equation
            eqSplitter = eqArrowMatches[0].end()    #Split the line at the first arrow
            #Make sure no more than one reaction constant is specified
            if len(eqConstantMatches) > 1:
                raise ParsingSyntaxError("ERROR: The parser found more than one reaction constant in line " + str(i) + ":\n" + line)
            else:
                try:
                    constant = float(ast.literal_eval(eqConstantMatches[0].group(1))) #Set the constant equal to the match that was found
                except ValueError:   
                    raise ParsingSyntaxError("ERROR: The parser was not able to read the molecule count in line " + str(i) + ":\n" + line)
            for match in (eqArrowMatches + eqPlusMatches + eqEndMatches):
                #If coefficient is not found, then set it equal to one
                if match.group(1) == '' or match.group(1) == None:
                    coefficient = 1
                else:
                    coefficient = int(match.group(1))
                elementName = match.group(2)
                if match.start() < eqSplitter:
                    if elementName in reactants:
                        raise ParsingSyntaxError("ERROR: The parser found more than one of the same reactant in line " + str(i) + ":\n" + line)
                    else:
                        products[elementName] = 0
                        reactants[elementName] = coefficient
                elif match.start() >= eqSplitter:
                    if elementName in products and products[elementName] != 0:
                        raise ParsingSyntaxError("ERROR: The parser found more than one of the same product in line " + str(i) + ":\n" + line)
                    else:
                        if not elementName in reactants:
                            reactants[elementName] = 0
                        products[elementName] = coefficient
            for reactant in reactants.keys():
                netChange[reactant] = products[reactant] - reactants[reactant]
            equations.append((constant, reactants, netChange))
        else:   #If the line is a definition
            try:
                moleCount = float(declarationMatches[0].group(2))
            except ValueError as e:
                raise ParsingSyntaxError("ERROR: The parser was not able to read the molecule count in line " + str(i) + ":\n" + line + ".\n" + e.args[0])
            elementName = declarationMatches[0].group(1)
            moleCounts[elementName] = moleCount
    return equations, moleCounts

#include <iostream>
#include <ctime>
#include <cctype>
#include <fstream>
#include <vector>
#include <sstream>
#include <map>
#include <functional>
#include <boost/regex.hpp>

// Compilation parameters
// g++ -I /usr/lib/boost/include -L /usr/lib/boost/lib -std=c++0x reg.cpp -lboost_regex -o reg

using std::string;
using std::vector;

typedef vector<string> TokensTable;

TokensTable keywordTable = {"program", "begin", "end", "var", "true", "false",
                            "ass", "if", "else", "then", "for", "to", "do",
                            "while", "read", "write", "int", "float", "bool",
                            "and", "or", "not"};    

TokensTable separatorTable = {"+", "-", "=", "<", ">", "*", 
                              "/", "(", ")", ";", ".", ":",
                              "<=", ">=", "<>", ","};   
TokensTable numberTable;
TokensTable idTable;

boost::regex bin_pattern("(0|1)+(B|b)");
boost::regex oct_pattern("[0-7]+(O|o)");
boost::regex dec_pattern("[0-9]+(D|d)?");
boost::regex hex_pattern("[0-9]+[A-Fa-f0-9]+(H|h)");
boost::regex dot_pattern("(\\.[0-9]+((E|e)(\\+|\\-)?[0-9]+)?)|([0-9]+(\\.[0-9]+)?((E|e)(\\+|\\-)?[0-9]+)?)");

constexpr int KEYWORD_TABLE_NUMBER   = 1;
constexpr int SEPARATOR_TABLE_NUMBER = 2;
constexpr int NUMBER_TABLE_NUMBER    = 3;
constexpr int ID_TABLE_NUMBER        = 4;

enum TypeChar  {CHAR_LETTER, CHAR_SEPARATOR, CHAR_DIGIT, CHAR_ERROR};
enum TypeToken {TOKEN_ID, TOKEN_SEPARATOR, TOKEN_NUMBER, COMMENT, END_COMMENT, TOKEN_ERROR};

TypeToken tokenType;

string inputString;       
string tokensBuffer;
vector<vector<int>> analyzeResult;
string error_message;
int error_line;
char currentChar;
int charNumber;   

bool isSeparator(char c)
{
    return c == '+' || c == '-' || c == '=' ||
           c == '<' || c == '>' || c == '/' ||
           c == '*' || c == ';' || c == '.' ||
           c == '(' || c == ')' || c == ':' || c == ',';
}

TypeChar typeChar(char c)
{
    if (isdigit(c))
        return CHAR_DIGIT;
    if (isalpha(c))
        return CHAR_LETTER;
    if (isSeparator(c))
        return CHAR_SEPARATOR;
    return CHAR_ERROR;
}

inline bool isHex(char c)
{
    return (c >= 'A' && c <= 'F') ||
           (c >= 'a' && c <= 'f');
}

inline bool isDot(char c)
{
    return c == '.';
}

void nextChar()
{
    currentChar = inputString[charNumber++];
}

int recordTable(TokensTable * table)
{
    table->push_back(tokensBuffer);
    return table->size() - 1;
}

inline void recordResult(int lineNumber, int tableNumber, int tokenNumber)
{
    analyzeResult.push_back({lineNumber, tableNumber, tokenNumber});
}

int indexToken(TokensTable table)
{
    for (int i = 0; i < table.size(); i++)
        if (table[i] == tokensBuffer)
            return i;
    return -1;
} 

inline void addBuffer()
{
    tokensBuffer.push_back(currentChar);
    nextChar();
}

inline bool isEof()
{
    return charNumber > inputString.size();
}

inline void log(const string & message)
{
    error_message += "Error at [" + 
                     std::to_string(error_line) + "," + 
                     std::to_string(charNumber) + "]: " + message + "\n";
}

void parseNumber()
{
    tokenType = TOKEN_NUMBER;

    while (!isEof() && (isdigit(currentChar) || isHex(currentChar) || isDot(currentChar)))
        addBuffer();

    if (!isEof())
        if (currentChar == 'H' || currentChar == 'h' ||
            currentChar == 'O' || currentChar == 'o')
        {
            addBuffer();
        }

    if (!isEof() && (currentChar == '+' || currentChar == '-') &&
                    (tokensBuffer.back() == 'E' || tokensBuffer.back() == 'e'))
    {
        addBuffer();
        if (!isEof() && isdigit(currentChar))
            while (!isEof() && (isdigit(currentChar) || isHex(currentChar) || isDot(currentChar)))
                addBuffer();
        else
            tokensBuffer.pop_back();
    }

    if (!boost::regex_match(tokensBuffer, bin_pattern) &&
        !boost::regex_match(tokensBuffer, oct_pattern) &&
        !boost::regex_match(tokensBuffer, dec_pattern) &&
        !boost::regex_match(tokensBuffer, hex_pattern) &&
        !boost::regex_match(tokensBuffer, dot_pattern))
    {
        log("\'" + tokensBuffer + "\'" + string(" undefined identificator."));
    }
}

void parseDot()
{
    addBuffer();
    if (!isEof() && isdigit(currentChar))
    {
        parseNumber();
        return;
    }
    if (isEof() || !isdigit(currentChar))
        tokenType = TOKEN_SEPARATOR;
}

void parseId()
{
    tokenType = TOKEN_ID;
    do
    {
        addBuffer();
    } while (!isEof() && (isalpha(currentChar) || isdigit(currentChar)));
}

void parseComment()
{
    tokenType = COMMENT;
    while (!isEof())
    {
        if (currentChar == '*') {
            nextChar();
            if (!isEof() && currentChar == '/')
            {
                tokenType = END_COMMENT;
                nextChar();
                return;
            }
        }
        else nextChar();
    }
}

void parseSeparator()
{
    tokenType = TOKEN_SEPARATOR;
    switch (currentChar)
    {
        case '+':
        case '-':
        case '*':
        case '=':
        case ';':
        case '(':
        case ')':
        case ':':
        case ',':
            addBuffer();
            break;
        case '<':
            addBuffer();
            if (currentChar == '>' || currentChar == '=')
            {
                addBuffer();
            }
            break;
        case '>':
            addBuffer();
            if (currentChar == '=')
                addBuffer();
            break;
        case '/':
            addBuffer();
            if (currentChar == '*')
            {
                tokensBuffer.clear();
                parseComment();
            }
            break;
        case '.':
            parseDot();
            break;
        default:
            addBuffer();
            log("\'" + tokensBuffer + "\'" + string(" undefined identificator."));
    }
}


void parseToken()
{
    if (tokenType != COMMENT)
        switch (typeChar(currentChar))
        {
            case CHAR_DIGIT:
                parseNumber();
                break;
            case CHAR_LETTER:
                parseId();
                break;
            case CHAR_SEPARATOR:
                parseSeparator();
                break;
            default:
                addBuffer();
                log("\'" + tokensBuffer + "\'" + string(" undefined identificator."));
        }
    else
        parseComment();
}

void parseLine()
{
    nextChar();
    do
    {
        while (currentChar == ' ') nextChar();
        if (isEof()) return;
        parseToken();
        if (tokensBuffer.empty()) continue;

        int index;
        switch (tokenType)
        {
            case TOKEN_NUMBER:
                index = indexToken(numberTable);
                if (index == -1)
                    index = recordTable(&numberTable);
                recordResult(error_line, NUMBER_TABLE_NUMBER, index);
                break;
            case TOKEN_ID:
                index = indexToken(keywordTable);
                if (index == -1)
                {
                    index = indexToken(idTable);
                    if (index == -1)
                        index = recordTable(&idTable);
                    recordResult(error_line, ID_TABLE_NUMBER, index);
                }
                else
                    recordResult(error_line, KEYWORD_TABLE_NUMBER, index);
                break;
            case TOKEN_SEPARATOR:
                recordResult(error_line, SEPARATOR_TABLE_NUMBER, indexToken(separatorTable));
                break;
            case COMMENT:
            case END_COMMENT:
                break;
            default:
                log(tokensBuffer + ": undefined identificator");
        }
        if (!tokensBuffer.empty()) tokensBuffer.clear();
    } while (!isEof());
}

void parse(const string & ifile)
{
    std::ifstream file(ifile);
    if (!file) 
    {
        error_message = "Error: file \'" + ifile + "\' is not exist";
        return;
    }
    while (std::getline(file, inputString))
    {
        error_line++;
        charNumber = 0;
        parseLine();
    }
    file.close();
}

int main(int argc, char *argv[])
{
    parse(argv[1]);

    if (!error_message.empty())
    {
        std::cerr << error_message;
        return -1;
    }

    std::ofstream file(argv[2]);

    for (auto item : numberTable)
        file << item << " ";
    file << "\n";

    for (auto item : idTable)
        file << item << " ";
    file << "\n";

    for (auto item : analyzeResult)
        file << std::to_string(item[0]) + string(",") + std::to_string(item[1]) + "," + std::to_string(item[2]) + " ";
    file << "\n";

    file.close();

    file.open("lexer.logs");
    file << "[Identificators]\n";
    for (int i = 0; i < idTable.size(); i++)
        file << i << ": " << idTable[i] << std::endl;

    file << "\n[Numbers]\n";
    for (int i = 0; i < numberTable.size(); i++)
        file << i << ": " << numberTable[i] << std::endl;

    file << "\n[Tokens]\n";
    for (int i = 0; i < analyzeResult.size(); i++)
        file << "(" << analyzeResult[i][1] << "," << analyzeResult[i][2] << ") : " 
             << (analyzeResult[i][1] == 1 ? keywordTable   [analyzeResult[i][2]] :
                 analyzeResult[i][1] == 2 ? separatorTable [analyzeResult[i][2]] :
                 analyzeResult[i][1] == 3 ? numberTable    [analyzeResult[i][2]] :
                                            idTable        [analyzeResult[i][2]]) << std::endl;
    file.close();
    return 0;
}

import struct, os

def read_text_file(file_name):
    """
    """


    file_list = []
    
    # NOTE: Remember to see the consequences of using utf-8-sig
    #       when reading and writing these text files.
    # NOTE: Shouldn't this try to detecct the actual encoding
    #       of the file instead of just opening it as UTF-8?
    # NOTE: Make sure to deal correctly with the BOM.
    # NOTE: What the block inside the 'with' statement does
    #       exactly the same as simply doing
    #       file_list = in_file.readlines(), it would be a good idea
    #       to first time the execution and see the differences
    #       in memory usage before making any changes.
    with open(file_name, 'r', encoding='utf-8-sig') as in_file:
        for line in in_file:
            file_list.append(line)

    return file_list

def hash_file(name):
    original_path = os.getcwd()

    dissected = name.split('\\')

    if ''.join(dissected) != name:
        path = '\\'.join(dissected[:-1])
        video_name = dissected[-1]
        os.chdir(path)
    
    else:
        video_name = name

    try:
                
        longlongformat = '<q'  # little-endian long long
        bytesize = struct.calcsize(longlongformat)
            
        f = open(video_name, "rb")
            
        filesize = os.path.getsize(video_name)
        hash = filesize
            
        if filesize < 65536 * 2:
            os.chdir(original_path)
            return "SizeError" 
        
        for x in range(int(65536/bytesize)):
            buffer = f.read(bytesize)
            (l_value,)= struct.unpack(longlongformat, buffer)
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number
                    
        f.seek(max(0,filesize-65536),0)
        for x in range(int(65536/bytesize)):
            buffer = f.read(bytesize)
            (l_value,)= struct.unpack(longlongformat, buffer)
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF
            
        f.close()
        returnedhash =  "%016x" % hash
        os.chdir(original_path)
        return returnedhash 

    except(IOError):
        os.chdir(original_path)
        return "IOError"

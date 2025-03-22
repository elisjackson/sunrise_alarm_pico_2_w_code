import gc
import uasyncio


def get_memory(server):

    gc.collect()
    mem_free = round(gc.mem_free() / 1000)
    print(str(mem_free), "kB")
    return f"{str(mem_free)} kB"
        

def format_time_str(datetime):
    
    t_dict = {
        "d": datetime[2],
        "M": datetime[1],
        "yyyy": datetime[0],
        "h": datetime[4],
        "m":datetime[5],
        "s": datetime[6],
        }
    
    t = {}
    
    for key in t_dict:
        val_str = str(t_dict[key])
        if key == "yyyy":
            t[key] = val_str[-2:]
        else:
            if len(val_str) == 1:
                # add leading 0
                t[key] = f"0{val_str}"
            else:
                t[key] = val_str
    
    # return dd/mm/yy h:m:s
    return f"{t['d']}/{t['M']}/{t['yyyy']} {t['h']}:{t['m']}:{t['s']}"
        
        
def write_to_log(server, message: str = ""):
    
    file = open("log.csv", "a")
    
    t = server.rtc.datetime()
    t_str = format_time_str(t)
    
    if not message:
        message = "Hello there!"
    
    write_str = f"{t_str} {message}\n"
    file.write(write_str)
    file.close()
        
        
async def write_memory_to_log(server):
    
    while True:
        memory_str = get_memory(server)
        write_to_log(server, message=memory_str)        
        await uasyncio.sleep(30 * 60)

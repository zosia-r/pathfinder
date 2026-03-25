
def sec_to_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02}:{m:02}:{s:02}"

def time_to_seconds(time_str):
    if len(time_str.split(':')) == 2:
        time_str += ":00"
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s
def gps_conversion(old):
    direction = {'N': -1, 'S': 1, 'E': -1, 'W': 1}
    new = old.replace('deg', ' ').replace('\'', ' ').replace('"', ' ')
    new = new.split()
    new_dir = new.pop()
    new.extend([0, 0, 0])
    return (int(new[0]) + int(new[1]) / 60.0 + float(new[2]) / 3600.0) * direction[new_dir]


if __name__ == '__main__':
    lat, lon = '''18 deg 27' 18.59" E#34 deg 11' 40.81" S'''.split('#')
    print(gps_conversion(lat), gps_conversion(lon))

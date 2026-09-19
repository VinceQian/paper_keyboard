def add(x,y):
    add = x+y
    return add

def main():
    # n = add(1,2)
    # print(n)
    
    test = [1,2,3]
    frame = {
      "frame_id": 1464,
      "t": 97.402,
      "fingers": [
        {
          "id": "index",
          "x": 239.7,
          "y": 90.15
        }
      ],
      "tap": {
        "audio": True
      }
    }
    print(frame["fingers"][0]["x"])


if __name__ == "__main__":
    main()
def main() -> None:
    print("it started", flush=True)

    for i in range(3):
        print(f"loop number {i}", flush=True)

    print("it finished", flush=True)


if __name__ == "__main__":
    main()

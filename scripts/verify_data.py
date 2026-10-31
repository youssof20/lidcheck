from lidcheck.io import archive_checksums, load_data

if __name__ == "__main__":
    print(archive_checksums())
    data=load_data()
    assert not data.duplicated(["dataset","patient"]).any()
    print(data.groupby("dataset").size())

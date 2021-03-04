use std::{
    ffi::OsStr,
    io,
    path::{Path, PathBuf},
};

extern crate tempfile;

#[derive(Debug)]
pub struct Object {
    pub root: PathBuf,
}

#[derive(Debug)]
pub struct ObjectStore {
    pub root: PathBuf,

    objs: PathBuf,
    refs: PathBuf,
    temp: PathBuf,

    work: tempfile::TempDir,
}

impl ObjectStore {
    pub fn new<S: AsRef<OsStr> + ?Sized>(root: &S) -> Result<Self, io::Error> {
        let root = PathBuf::from(root);
        let objs = root.join("objets");
        let refs = root.join("refs");
        let tmp = root.join("tmp");

        std::fs::create_dir_all(&objs)?;
        std::fs::create_dir_all(&refs)?;
        std::fs::create_dir_all(&tmp)?;

        let work = tempfile::Builder::new().prefix("work").tempdir_in(&tmp)?;

        let store = ObjectStore {
            root: root,

            objs: objs,
            refs: refs,
            temp: tmp,

            work: work,
        };

        Ok(store)
    }
}

fn main() -> Result<(), std::io::Error> {
    let mut store = ObjectStore::new("/var/cache/osbuild/store")?;

    println!("Store at {:?}", store.root);

    Ok(())
}

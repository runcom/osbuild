use libc;
use std::env;
use std::ffi::OsStr;
use std::io;
use std::os::unix::ffi::{OsStrExt, OsStringExt};
use std::path::{Path, PathBuf};

pub struct TempDir(PathBuf);

impl TempDir {
    pub fn create_at<S: AsRef<OsStr> + ?Sized>(
        root: &S,
        prefix: Option<&str>,
    ) -> Result<Self, io::Error> {
        let ret = TempDir(PathBuf::from(root.as_ref()));
        Ok(ret)
    }
}

pub fn mkdtemp() -> Result<PathBuf, io::Error> {
    let mut tmp = env::temp_dir();
    tmp.push("osbuild-oxi.XXXXXX\0");

    let mut data = tmp.into_os_string().into_vec();

    let r = unsafe { libc::mkdtemp(data.as_mut_ptr() as *mut libc::c_char) as *const libc::c_char };

    assert!(!r.is_null());

    if r.is_null() {
        Err(io::Error::last_os_error())
    } else {
        data.pop();
        Ok(Path::new(OsStr::from_bytes(&data)).to_path_buf())
    }
}

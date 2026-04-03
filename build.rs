use libbpf_cargo::SkeletonBuilder;
use std::env;
use std::path::PathBuf;

fn generate_skeleton(out: &mut PathBuf, name: &str) {
    let c_path = format!("src/bpf/{}.bpf.c", name);
    let rs_name = format!("{}.skel.rs", name);
    out.push(&rs_name);
    SkeletonBuilder::new()
        .source(&c_path)
        .build_and_generate(&out)
        .unwrap();

    out.pop();
    println!("cargo:rerun-if-changed={c_path}");
}

fn generate_header(out: &mut PathBuf, name: &str) {
    let header_path = format!("src/bpf/{}.h", name);
    let rs_name = format!("{}.rs", name);

    out.push(&rs_name);
    let bindings = bindgen::Builder::default()
        .header(&header_path)
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .unwrap();
    bindings.write_to_file(&out).unwrap();
    out.pop();

    println!("cargo:rerun-if-changed={header_path}");
}

fn main() {
    let mut out =
        PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR must be set in build script"));

    generate_skeleton(&mut out, "sslsniff");
    generate_header(&mut out, "sslsniff");
    
    // Generate proctrace skeleton and bindings
    generate_skeleton(&mut out, "proctrace");
    generate_header(&mut out, "proctrace");
    
    // Generate procmon skeleton and bindings
    generate_skeleton(&mut out, "procmon");
    generate_header(&mut out, "procmon");
    
    // generate_header(&mut out, "frametypes");
    // generate_header(&mut out, "errors");
    // generate_header(&mut out, "stackdeltatypes");

    // 确保 frontend-dist 目录存在，避免 include_dir! 宏在编译期因目录不存在而 panic
    // 前端构建产物放入该目录后重新编译即可嵌入
    let manifest_dir = env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR must be set");
    let frontend_dist = PathBuf::from(&manifest_dir).join("frontend-dist");
    if !frontend_dist.exists() {
        std::fs::create_dir_all(&frontend_dist)
            .expect("Failed to create frontend-dist directory");
    }
    println!("cargo:rerun-if-changed=frontend-dist");
}
